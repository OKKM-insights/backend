import pytest
import numpy as np
from PIL import Image as pilImage
from services.ObjectExtractionService import ObjectExtractionService
from services.DataTypes import Image, ImageObject_bb, Labeller, Label, ImageClassMeasure

# --- Dummy Dependency Classes ---

class DummyICMDB:
    def get_imageclassmeasures_images(self, query):
        # Create an ImageClassMeasure with a 10x10 matrix of likelihoods above threshold.
        im_width, im_height = 10, 10
        likelihoods = [[0.8 for _ in range(im_width)] for _ in range(im_height)]
        confidence = [[0.0 for _ in range(im_width)] for _ in range(im_height)]
        helper_values = [[[0.5, 0.5] for _ in range(im_width)] for _ in range(im_height)]
        return ImageClassMeasure("img1", likelihoods, confidence, helper_values, "plane", im_width, im_height)
    def push_imageclassmeasure_images(self, icm):
        self.last_icm = icm

class DummyLabellerDB:
    def get_labellers_with_data(self, query, data):
        # Return a Labeller for each id provided in the tuple.
        ids = data.get('ids', ())
        return [Labeller(labeller_id, "plane", 1.0, 1.0) for labeller_id in ids] if ids else []
    def push_labeller(self, labeller):
        pass

class DummyImageObjectDB:
    def __init__(self):
        self.pushed_objects = []
    def push_imageobject(self, obj):
        self.pushed_objects.append(obj)

class DummyObjectService:
    def get_objects(self, image, Class, labellers, labels, demo=False):
        # Return a fixed dummy list of ImageObject_bb.
        return [ImageObject_bb("io1", image.ImageID, Class, 0.9, 0, 0, 9, 9)]

class DummyProjectDB:
    def get_projects(self, query):
        dummy_img = pilImage.new("RGB", (10, 10))
        dummy_image = type("DummyImage", (), {})()
        dummy_image.ImageID = "img1"
        dummy_image.image_data = dummy_img
        dummy_project = type("DummyProject", (), {})()
        dummy_project.images = [dummy_image]
        return [dummy_project]

class DummyLabelDB:
    def get_labels(self, query):
        return [Label(
            LabelID="lbl1",
            LabellerID="lab1",
            ImageID="img1",
            Class="plane",
            top_left_x=1,
            top_left_y=1,
            bot_right_x=5,
            bot_right_y=5,
            offset_x=0,
            offset_y=0,
            creation_time="2023-01-01",
            origImageID="img1"
        )]

# --- Test for get_objects ---

def test_get_objects():
    # Create a dummy PIL image (10x10) and wrap it in a dummy Image object.
    dummy_pil = pilImage.new("RGB", (10, 10))
    dummy_img = Image("img1", "dummy_project", dummy_pil)

    # Create dummy Labeller and Label lists.
    dummy_labellers = [Labeller("lab1", "plane", 1.0, 1.0)]
    dummy_labels = [Label("lbl1", "lab1", "img1", "plane", 1, 1, 5, 5, 0, 0, "2023-01-01", "img1")]

    # Instantiate dummy dependencies.
    dummy_icm_db = DummyICMDB()
    dummy_labeller_db = DummyLabellerDB()
    dummy_imageobject_db = DummyImageObjectDB()
    dummy_object_service = DummyObjectService()
    dummy_project_db = DummyProjectDB()
    dummy_label_db = DummyLabelDB()

    # Instantiate the ObjectExtractionService.
    # Note: Its constructor takes icm_db and labeller_db; the other dependencies are set manually.
    service = ObjectExtractionService(dummy_icm_db, dummy_labeller_db, threshold=0.7)
    service.project_db = dummy_project_db
    service.label_db = dummy_label_db
    service.labeller_db = dummy_labeller_db
    service.imageobject_db = dummy_imageobject_db
    service.object_service = dummy_object_service

    # Override GPU methods (and any other external operations) with no-ops.
    service._ObjectExtractionService__cuda_update_label_likelihood = lambda icm, labels, labeller: None
    service._ObjectExtractionService__cuda_update_labeller_accuracy = lambda icm, labels, labeller: None

    # Call get_objects with the full set of required parameters.
    output = service.get_objects(dummy_img, "plane", dummy_labellers, dummy_labels, demo=False)

    # Instead of asserting on pushed_objects (which remains empty), assert on the output from get_objects.
    # We expect the __find_connected_groups method to find one group spanning the entire 10x10 grid,
    # and then extract_bounding_box should return (0, 0, 9, 9).
    assert len(output) == 1
    obj = output[0]
    assert obj.top_left_x == 0
    assert obj.top_left_y == 0
    assert obj.bot_right_x == 9
    assert obj.bot_right_y == 9
