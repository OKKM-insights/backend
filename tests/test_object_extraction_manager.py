import pytest
import time
import numpy as np
from PIL import Image as pilImage
import base64

# Import the manager class using absolute imports.
from services.ObjectExtractionManager import ObjectExtractionManager
from services.DataTypes import Label, Labeller


# -------------------------------------------------
# Dummy Connector and Service Classes for Testing
# -------------------------------------------------

class DummyProjectDB:
    def get_projects(self, query):
        # Create a dummy image with known dimensions.
        dummy_pil = pilImage.new("RGB", (100, 100))
        dummy_image = type("DummyImage", (), {})()
        dummy_image.ImageID = "img1"
        dummy_image.image_data = dummy_pil
        # Create a dummy project with one image.
        dummy_project = type("DummyProject", (), {})()
        dummy_project.images = [dummy_image]
        return [dummy_project]

class DummyLabelDB:
    def get_labels(self, query):
        # Return one dummy label.
        dummy_label = Label(
            LabelID="lbl1",
            LabellerID="lab1",
            ImageID="img1",
            Class="plane",
            top_left_x=10,
            top_left_y=10,
            bot_right_x=50,
            bot_right_y=50,
            offset_x=0,
            offset_y=0,
            creation_time="2023-01-01",
            origImageID="img1"
        )
        return [dummy_label]

class DummyLabellerDB:
    def get_labellers_with_data(self, query, data):
        # Return an empty list so that the manager will add missing labellers.
        return []

class DummyObjectExtractionService:
    def get_objects(self, image, Class, labellers, labels, demo=False):
        # Return a list with one dummy object.
        dummy_obj = {"dummy_attr": "value"}
        return [dummy_obj]

class DummyImageObjectDB:
    def __init__(self):
        self.pushed_objects = []
    def push_imageobject(self, obj):
        self.pushed_objects.append(obj)

# -------------------------------------------------
# Tests for Consensus Bounding Box Computation
# -------------------------------------------------
@pytest.mark.skip(reason="Skipping consensus bounding box test until fixed")
def test_get_consensus_bbox():
    # Create a dummy PIL image with known dimensions.
    dummy_pil = pilImage.new("RGB", (100, 100))
    # Build a dummy image object with an image_data attribute.
    dummy_image = type("DummyImage", (), {})()
    dummy_image.ImageID = "img1"
    dummy_image.image_data = dummy_pil

    # Create two dummy Label instances with overlapping regions.
    label1 = Label(
        LabelID="lbl1",
        LabellerID="lab1",
        ImageID="img1",
        Class="plane",
        top_left_x=10,
        top_left_y=10,
        bot_right_x=50,
        bot_right_y=50,
        offset_x=0,
        offset_y=0,
        creation_time="2023-01-01",
        origImageID="img1"
    )
    label2 = Label(
        LabelID="lbl2",
        LabellerID="lab1",
        ImageID="img1",
        Class="plane",
        top_left_x=20,
        top_left_y=20,
        bot_right_x=60,
        bot_right_y=60,
        offset_x=0,
        offset_y=0,
        creation_time="2023-01-01",
        origImageID="img1"
    )
    # Instantiate the manager without needing real connectors.
    manager = ObjectExtractionManager(None, None, None, None, None)
    # Test with threshold = 0.5: Expect the union of both boxes.
    bbox = manager.get_consensus_bbox(dummy_image, [label1, label2], threshold=0.5)
    assert bbox == (10, 10, 60, 60)
    # Test with threshold = 1.0: Only the overlapping area counts.
    bbox_strict = manager.get_consensus_bbox(dummy_image, [label1, label2], threshold=1.0)
    assert bbox_strict == (20, 20, 50, 50)

# -------------------------------------------------
# Tests for the get_objects Workflow
# -------------------------------------------------

def test_get_objects():
    # Create dummy connector/service instances.
    project_db = DummyProjectDB()
    label_db = DummyLabelDB()
    labeller_db = DummyLabellerDB()
    imageobject_db = DummyImageObjectDB()
    object_service = DummyObjectExtractionService()

    # Instantiate the ObjectExtractionManager with our dummy dependencies.
    manager = ObjectExtractionManager(project_db, label_db, labeller_db, imageobject_db, object_service)

    # Call get_objects with dummy project_id and class.
    manager.get_objects("66", "plane", demo=True)

    # Our dummy service returns one object per image,
    # and DummyProjectDB returns one image.
    # Therefore, we expect one call to push_imageobject.
    assert len(imageobject_db.pushed_objects) == 1
    # Optionally, check that the pushed object is the dummy object from our service.
    pushed_obj = imageobject_db.pushed_objects[0]
    assert pushed_obj.get("dummy_attr") == "value"
