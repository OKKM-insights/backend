import uuid
import pytest
from PIL import Image as pilImage
from services.DataTypes import (
    Label,
    Labeller,
    ImageObject,
    Image,
    Project,
    ImageClassMeasure
)

# --- Tests for Label ---

def test_label_auto_uuid():
    # When LabelID is not provided, it should auto-generate a valid UUID.
    label = Label(
        LabellerID="lab1",
        ImageID="img1",
        Class="cat",
        top_left_x=10,
        top_left_y=10,
        bot_right_x=20,
        bot_right_y=20,
        offset_x=0,
        offset_y=0,
        creation_time="2025-03-10",
        origImageID="orig1"
    )
    # Check that the LabelID is auto-generated and is a valid UUID.
    try:
        uuid_obj = uuid.UUID(label.LabelID)
    except ValueError:
        pytest.fail("LabelID is not a valid UUID")
    # Verify some other attributes.
    assert label.LabellerID == "lab1"
    assert label.ImageID == "img1"
    assert label.Class == "cat"

def test_label_given_uuid():
    # If a LabelID is provided, it should be used.
    custom_id = "custom-id-123"
    label = Label(
        LabelID=custom_id,
        LabellerID="lab1",
        ImageID="img1",
        Class="dog",
        top_left_x=0,
        top_left_y=0,
        bot_right_x=100,
        bot_right_y=100,
        offset_x=5,
        offset_y=5,
        creation_time="2025-03-10",
        origImageID="orig2"
    )
    assert label.LabelID == custom_id

# --- Tests for Labeller ---

def test_labeller_defaults():
    # Check that default alpha and beta values are set.
    labeller = Labeller(LabellerID="l1", skill="expert")
    assert labeller.alpha == 1.2
    assert labeller.beta == 1

def test_labeller_custom():
    # Test custom values for alpha and beta.
    labeller = Labeller(LabellerID="l2", skill="novice", alpha=2.5, beta=3.5)
    assert labeller.alpha == 2.5
    assert labeller.beta == 3.5

# --- Tests for ImageObject ---

def test_imageobject_defaults():
    # Without providing ImageObjectID, related_pixels, or related_labels.
    image_object = ImageObject(ImageID="img1", Class="dog", Confidence=0.9)
    # Auto-generated ImageObjectID should be set.
    assert image_object.ImageObjectID is not None
    # related_pixels and related_labels should default to empty lists.
    assert image_object.related_pixels == []
    assert image_object.related_labels == []

def test_imageobject_custom():
    # Test with custom related_pixels and related_labels.
    label = Label(
        LabellerID="lab1",
        ImageID="img1",
        Class="cat",
        top_left_x=10,
        top_left_y=10,
        bot_right_x=50,
        bot_right_y=50,
        offset_x=0,
        offset_y=0,
        creation_time="2025-03-10",
        origImageID="orig1"
    )
    pixels = [[10, 20], [30, 40]]
    labels = [label]
    image_object = ImageObject(
        ImageID="img1",
        Class="cat",
        Confidence=0.95,
        related_pixels=pixels,
        related_labels=labels
    )
    assert image_object.related_pixels == pixels
    assert image_object.related_labels == labels

# --- Tests for Image ---

def test_image_initialization():
    # Create a simple PIL image.
    img = pilImage.new('RGB', (10, 10), color='white')
    image = Image(ImageID="img1", ProjectID="proj1", image_data=img)
    assert image.ImageID == "img1"
    assert image.ProjectID == "proj1"
    assert image.image_data == img

# --- Tests for Project ---

def test_project_initialization():
    img = pilImage.new('RGB', (10, 10), color='white')
    image = Image(ImageID="img1", ProjectID="proj1", image_data=img)
    project = Project(ProjectID="proj1", classes=["cat", "dog"], images=[image])
    assert project.ProjectID == "proj1"
    assert project.classes == ["cat", "dog"]
    assert project.images == [image]

# --- Tests for ImageClassMeasure ---

def test_imageclassmeasure_defaults():
    # Test that default likelihoods, confidence, and helper_values are correctly set.
    width, height = 5, 5
    icm = ImageClassMeasure(
        imageID="img1",
        likelihoods=None,
        confidence=None,
        helper_values=None,
        label="background",
        im_width=width,
        im_height=height
    )
    # likelihoods should be a matrix of 0.5
    assert len(icm.likelihoods) == height
    for row in icm.likelihoods:
        assert len(row) == width
        assert all(val == 0.5 for val in row)
    # confidence should be a matrix of 0.0
    assert len(icm.confidence) == height
    for row in icm.confidence:
        assert len(row) == width
        assert all(val == 0.0 for val in row)
    # helper_values should be a matrix of [0.5, 0.5] lists.
    assert len(icm.helper_values) == height
    for row in icm.helper_values:
        assert len(row) == width
        for helper in row:
            assert helper == [0.5, 0.5]

def test_imageclassmeasure_custom():
    # Provide custom matrices and ensure they are set as provided.
    width, height = 3, 3
    likelihoods = [[0.1] * width for _ in range(height)]
    confidence = [[0.9] * width for _ in range(height)]
    helper_values = [[[0.2, 0.8] for _ in range(width)] for _ in range(height)]
    icm = ImageClassMeasure(
        imageID="img2",
        likelihoods=likelihoods,
        confidence=confidence,
        helper_values=helper_values,
        label="object",
        im_width=width,
        im_height=height
    )
    assert icm.likelihoods == likelihoods
    assert icm.confidence == confidence
    assert icm.helper_values == helper_values
