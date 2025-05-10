import json
import pytest
from services.ReportGenerator import ReportGenerator
from services.DataTypes import Labeller  # For type-checking, if needed
from PIL import Image as pilImage

# --- Dummy Connector Classes ---

class DummyProjectDB:
    def get_projects(self, query: str):
        """
        Returns one dummy project with one image.
        The project has:
          - ProjectID: "proj1"
          - classes: ["plane"]
          - images: a list with one Image (ID "img1")
          - end_date: "2023-12-31"
        """
        from services.DataTypes import Project, Image
        # Create a dummy PIL image (10x10, blue)
        dummy_img = pilImage.new("RGB", (10, 10), color="blue")
        image = Image("img1", "proj1", dummy_img)
        return [Project("proj1", ["plane"], [image], "2023-12-31")]

class DummyLabelDB:
    def get_labels(self, query: str):
        """
        Returns two dummy labels for an image.
        Two labels for image "img1" (both for class "plane") from different labellers.
        They are returned in descending order by creation_time so that the most recent one comes first.
        """
        from services.DataTypes import Label
        # Create two labels with creation times such that the most recent is first.
        label1 = Label("lbl1", "lab1", "img1", "plane", 10, 10, 50, 50, 0, 0, "2023-01-01", "img1")
        label2 = Label("lbl2", "lab2", "img1", "plane", 15, 15, 55, 55, 0, 0, "2023-01-02", "img1")
        # Return in descending order by creation_time (label2 is most recent)
        return [label2, label1]

class DummyLabellerDB:
    def get_labeller_info_with_data(self, query: str, data):
        """
        Returns dummy labeller objects for each labeller ID provided in data['ids'].
        For our test, if the IDs are ("lab1", "lab2"), return two Labeller objects.
        """
        from services.DataTypes import Labeller
        ids = data.get('ids', ())
        # Create a Labeller for each id.
        return [Labeller(labeller_id, "plane", 1.0, 1.0) for labeller_id in ids]

class DummyImageObjectDB:
    def push_imageobject(self, obj):
        # For report generation, pushing image objects is not used.
        pass

class DummyICMDB:
    # Not used in ReportGenerator.get_report_info.
    pass

# --- PyTest Fixture to Instantiate ReportGenerator with Dummies ---

@pytest.fixture
def dummy_report_generator():
    # Instantiate ReportGenerator. It creates real connector instances by default,
    # but we override them with our dummy classes.
    rg = ReportGenerator()
    rg.ProjectDatabaseConnector = DummyProjectDB()
    rg.LabelDatabaseConnector = DummyLabelDB()
    rg.LabellerDatabaseConnector = DummyLabellerDB()
    rg.ImageObjectDatabaseConnector = DummyImageObjectDB()
    rg.ICMDB = DummyICMDB()
    return rg

# --- Test Cases ---

def test_get_report_info(dummy_report_generator):
    """
    Tests ReportGenerator.get_report_info() by simulating a scenario with one project,
    one image, and two labels (from two different labellers).
    
    Expected behavior:
      - num_labels: 2
      - num_labellers: 2 (accumulated from all images)
      - num_images: 1
      - avg_num_labels: (2 / 1) / 2 = 1.0
      - project_end_date: "2023-12-31"
      - last_label_time: the most recent label time ("2023-01-02")
      - category_data: {"plane": 2}
      - top_labellers: keys "1" and "2" should have one label each, key "3" should be None.
    """
    # Call get_report_info with a dummy project_id (e.g., 1).
    report_json = dummy_report_generator.get_report_info(1)
    report = json.loads(report_json)
    
    # Verify scalar values.
    assert report['num_labels'] == 2
    assert report['num_labellers'] == 2
    assert report['num_images'] == 1
    assert report['avg_num_labels'] == 1.0
    assert report['project_end_date'] == "2023-12-31"
    assert report['last_label_time'] == "2023-01-02"
    assert report['category_data'] == {"plane": 2}
    
    # Verify the structure for top_labellers.
    top_labellers = report['top_labellers']
    assert "1" in top_labellers
    assert "2" in top_labellers
    assert "3" in top_labellers
    
    # For labellers "1" and "2", num_labels should be 1.
    assert top_labellers["1"]['num_labels'] == 1
    assert top_labellers["2"]['num_labels'] == 1
    # For key "3", both num_labels and user_info should be None.
    assert top_labellers["3"]['num_labels'] is None
    assert top_labellers["3"]['user_info'] is None

    # Optionally, verify that user_info for labeller "1" and "2" are represented.
    # (Depending on your Labeller __dict__ or __repr__, you might check for specific attributes.)
    assert top_labellers["1"]['user_info'] is not None
    assert top_labellers["2"]['user_info'] is not None
