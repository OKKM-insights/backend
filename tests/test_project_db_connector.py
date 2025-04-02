import io
import pytest
from PIL import Image as pilImage
from services.ProjectDatabaseConnector import MYSQLProjectDatabaseConnector
from services.DataTypes import Project, Image

# --- Dummy Result and Connection Classes ---

class DummyResult:
    def __init__(self, rows, rowcount):
        self.rows = rows
        self.rowcount = rowcount
    def __iter__(self):
        return iter(self.rows)

# Default dummy connection that simulates one project with one image.
class DummyConnection:
    def __init__(self):
        self.queries = []  # Record executed queries (optional)
    def execute(self, query, params=None):
        q = str(query)
        self.queries.append((q, params))
        if "FROM my_image_db.Projects" in q:
            # Simulate a single project row:
            # Columns: 0=project_id, 4=end_date, 5=categories string.
            row = ("proj1", "dummy", "dummy", "dummy", "2023-12-31", "class1,class2")
            return DummyResult([row], 1)
        elif "FROM OriginalImages" in q:
            if params and params.get("project_id") == "proj1":
                # Create a dummy 10x10 red image.
                dummy_img = pilImage.new("RGB", (10, 10), color="red")
                buf = io.BytesIO()
                dummy_img.save(buf, format="PNG")
                image_bytes = buf.getvalue()
                row = ("img1", "proj1", image_bytes)
                return DummyResult([row], 1)
            else:
                return DummyResult([], 0)
        else:
            return DummyResult([], 0)
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

# Dummy engine that returns our default DummyConnection.
class DummyEngine:
    def connect(self):
        return DummyConnection()

# --- Additional Dummy Connections for Specific Test Cases ---

# Test case: No projects returned.
class DummyConnectionEmpty:
    def __init__(self):
        self.queries = []
    def execute(self, query, params=None):
        q = str(query)
        self.queries.append((q, params))
        # Return no rows for any query.
        return DummyResult([], 0)
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class DummyEngineEmpty:
    def connect(self):
        return DummyConnectionEmpty()

# Test case: Project returned but no images found.
class DummyConnectionNoImages:
    def __init__(self):
        self.queries = []
    def execute(self, query, params=None):
        q = str(query)
        self.queries.append((q, params))
        if "FROM my_image_db.Projects" in q:
            row = ("proj2", "dummy", "dummy", "dummy", "2024-01-01", "class3")
            return DummyResult([row], 1)
        elif "FROM OriginalImages" in q:
            # Return empty result for images query.
            return DummyResult([], 0)
        else:
            return DummyResult([], 0)
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class DummyEngineNoImages:
    def connect(self):
        return DummyConnectionNoImages()

# Test case: Multiple projects with multiple images.
class DummyConnectionMulti:
    def __init__(self):
        self.queries = []
    def execute(self, query, params=None):
        q = str(query)
        self.queries.append((q, params))
        if "FROM my_image_db.Projects" in q:
            # Two project rows.
            row1 = ("proj1", "dummy", "dummy", "dummy", "2023-12-31", "class1,class2")
            row2 = ("proj2", "dummy", "dummy", "dummy", "2024-01-01", "class3,class4")
            return DummyResult([row1, row2], 2)
        elif "FROM OriginalImages" in q:
            if params and params.get("project_id") == "proj1":
                # Two images for proj1.
                dummy_img1 = pilImage.new("RGB", (10, 10), color="red")
                buf1 = io.BytesIO()
                dummy_img1.save(buf1, format="PNG")
                image_bytes1 = buf1.getvalue()
                dummy_img2 = pilImage.new("RGB", (20, 20), color="blue")
                buf2 = io.BytesIO()
                dummy_img2.save(buf2, format="PNG")
                image_bytes2 = buf2.getvalue()
                row1 = ("img1", "proj1", image_bytes1)
                row2 = ("img2", "proj1", image_bytes2)
                return DummyResult([row1, row2], 2)
            elif params and params.get("project_id") == "proj2":
                # One image for proj2.
                dummy_img = pilImage.new("RGB", (15, 15), color="green")
                buf = io.BytesIO()
                dummy_img.save(buf, format="PNG")
                image_bytes = buf.getvalue()
                row = ("img3", "proj2", image_bytes)
                return DummyResult([row], 1)
            else:
                return DummyResult([], 0)
        else:
            return DummyResult([], 0)
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class DummyEngineMulti:
    def connect(self):
        return DummyConnectionMulti()

# --- Test Cases ---

def test_get_projects_default(monkeypatch):
    """
    Test the default scenario: one project with one image.
    """
    monkeypatch.setattr("services.ProjectDatabaseConnector.create_engine", lambda url: DummyEngine())
    connector = MYSQLProjectDatabaseConnector()
    projects = connector.get_projects("SELECT * FROM my_image_db.Projects;")
    assert len(projects) == 1
    proj = projects[0]
    assert proj.ProjectID == "proj1"
    assert proj.classes == ["class1", "class2"]
    assert proj.end_date == "2023-12-31"
    assert len(proj.images) == 1
    img = proj.images[0]
    assert img.ImageID == "img1"
    # Check that image_data is a PIL image by verifying it has a size attribute.
    assert hasattr(img.image_data, "size")

def test_get_projects_empty(monkeypatch):
    """
    Test the scenario where no projects are returned.
    """
    monkeypatch.setattr("services.ProjectDatabaseConnector.create_engine", lambda url: DummyEngineEmpty())
    connector = MYSQLProjectDatabaseConnector()
    projects = connector.get_projects("SELECT * FROM my_image_db.Projects;")
    assert projects == []

def test_get_projects_no_images(monkeypatch):
    """
    Test when a project is returned but no images are found for that project.
    """
    monkeypatch.setattr("services.ProjectDatabaseConnector.create_engine", lambda url: DummyEngineNoImages())
    connector = MYSQLProjectDatabaseConnector()
    projects = connector.get_projects("SELECT * FROM my_image_db.Projects;")
    assert len(projects) == 1
    proj = projects[0]
    # Even though a project is returned, images should be an empty list.
    assert proj.images == []

def test_get_projects_multiple(monkeypatch):
    """
    Test multiple projects each with their own images.
    """
    monkeypatch.setattr("services.ProjectDatabaseConnector.create_engine", lambda url: DummyEngineMulti())
    connector = MYSQLProjectDatabaseConnector()
    projects = connector.get_projects("SELECT * FROM my_image_db.Projects;")
    assert len(projects) == 2

    # Validate first project.
    proj1 = projects[0]
    assert proj1.ProjectID == "proj1"
    assert proj1.classes == ["class1", "class2"]
    assert proj1.end_date == "2023-12-31"
    # proj1 should have 2 images.
    assert len(proj1.images) == 2
    assert proj1.images[0].ImageID == "img1"
    assert proj1.images[1].ImageID == "img2"

    # Validate second project.
    proj2 = projects[1]
    assert proj2.ProjectID == "proj2"
    assert proj2.classes == ["class3", "class4"]
    assert proj2.end_date == "2024-01-01"
    # proj2 should have 1 image.
    assert len(proj2.images) == 1
    assert proj2.images[0].ImageID == "img3"
