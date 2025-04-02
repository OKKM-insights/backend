import uuid
import pytest
from PIL import Image as pilImage
from services.DataTypes import (
    Label,
    Labeller,
    ImageObject,
    ImageObject_bb,
    Image,
    Project,
    ImageClassMeasure,
)

def test_label_uuid_generation():
    # Creating a Label without providing LabelID should generate one automatically.
    label = Label(
        LabellerID="lab1",
        ImageID="img1",
        Class="test",
        top_left_x=0,
        top_left_y=0,
        bot_right_x=10,
        bot_right_y=10,
        offset_x=0,
        offset_y=0,
        creation_time="2023-01-01",
        origImageID="orig1"
    )
    assert label.LabelID is not None
    try:
        uuid.UUID(label.LabelID)
    except Exception:
        pytest.fail("LabelID is not a valid UUID")

def test_label_provided_id():
    label_id = "test-id"
    label = Label(
        LabelID=label_id,
        LabellerID="lab1",
        ImageID="img1",
        Class="test",
        top_left_x=1,
        top_left_y=1,
        bot_right_x=11,
        bot_right_y=11,
        offset_x=1,
        offset_y=1,
        creation_time="2023-01-01",
        origImageID="orig1"
    )
    assert label.LabelID == label_id

def test_labeller_assignment():
    labeller = Labeller(LabellerID="lab1", skill="expert", alpha=2.0, beta=0.5)
    assert labeller.LabellerID == "lab1"
    assert labeller.skill == "expert"
    assert labeller.alpha == 2.0
    assert labeller.beta == 0.5

def test_image_object_uuid():
    # Creating an ImageObject without ImageObjectID should generate one.
    image_object = ImageObject(ImageID="img1", Class="test", Confidence=0.9)
    assert image_object.ImageObjectID is not None
    try:
        uuid.UUID(image_object.ImageObjectID)
    except Exception:
        pytest.fail("ImageObjectID is not a valid UUID")

def test_image_object_related():
    # Create a Label instance for use in the related_labels list.
    label = Label(
        LabellerID="lab1",
        ImageID="img1",
        Class="test",
        top_left_x=0,
        top_left_y=0,
        bot_right_x=5,
        bot_right_y=5,
        offset_x=0,
        offset_y=0,
        creation_time="2023-01-01",
        origImageID="orig1"
    )
    related_pixels = [[0, 0], [1, 1]]
    image_object = ImageObject(
        ImageID="img1",
        Class="test",
        Confidence=0.8,
        related_pixels=related_pixels,
        related_labels=[label]
    )
    assert image_object.related_pixels == related_pixels
    assert image_object.related_labels == [label]

def test_image_object_bb_uuid():
    # Creating an ImageObject_bb without ImageObjectID should generate one.
    image_object_bb = ImageObject_bb(
        ImageID="img1",
        Class="test",
        Confidence=0.75,
        top_left_x=0,
        top_left_y=0,
        bot_right_x=5,
        bot_right_y=5
    )
    assert image_object_bb.ImageObjectID is not None
    try:
        uuid.UUID(image_object_bb.ImageObjectID)
    except Exception:
        pytest.fail("ImageObjectID in ImageObject_bb is not a valid UUID")

def test_image_creation():
    # Create a simple PIL image.
    pil_img = pilImage.new("RGB", (10, 10), color="red")
    image_obj = Image(ImageID="img1", ProjectID="proj1", image_data=pil_img)
    assert image_obj.ImageID == "img1"
    assert image_obj.ProjectID == "proj1"
    assert image_obj.image_data == pil_img

def test_project_assignment():
    pil_img = pilImage.new("RGB", (10, 10), color="blue")
    image_obj = Image(ImageID="img1", ProjectID="proj1", image_data=pil_img)
    project = Project(ProjectID="proj1", classes=["class1", "class2"], images=[image_obj], end_date="2023-12-31")
    assert project.ProjectID == "proj1"
    assert project.classes == ["class1", "class2"]
    assert project.images == [image_obj]
    assert project.end_date == "2023-12-31"

def test_image_class_measure_defaults():
    # When likelihoods, confidence, and helper_values are not provided,
    # the default matrices/lists should be created.
    im_width = 5
    im_height = 3
    icm = ImageClassMeasure(
        imageID="img1",
        likelihoods=None,
        confidence=None,
        helper_values=None,
        label="test",
        im_width=im_width,
        im_height=im_height
    )
    # Check likelihoods default to 0.5.
    for row in icm.likelihoods:
        assert row == [0.5] * im_width
    # Check confidence default to 0.0.
    for row in icm.confidence:
        assert row == [0.0] * im_width
    # Check helper_values default: each element should be [0.5, 0.5].
    for row in icm.helper_values:
        for cell in row:
            assert cell == [0.5, 0.5]

def test_image_class_measure_assignment():
    # Test that provided matrices are correctly assigned.
    likelihoods = [[0.1, 0.2], [0.3, 0.4]]
    confidence = [[0.0, 1.0], [0.5, 0.5]]
    helper_values = [
        [[0.1, 0.9], [0.2, 0.8]],
        [[0.3, 0.7], [0.4, 0.6]]
    ]
    icm = ImageClassMeasure(
        imageID="img2",
        likelihoods=likelihoods,
        confidence=confidence,
        helper_values=helper_values,
        label="test",
        im_width=2,
        im_height=2
    )
    assert icm.likelihoods == likelihoods
    assert icm.confidence == confidence
    assert icm.helper_values == helper_values
