import os
import pytest
import uuid
import urllib.parse
from sqlalchemy import text

# Import the connector classes using absolute imports.
from services.ImageObjectDatabaseConnector_bb import (
    ImageObjectDatabaseConnector_bb,
    NoneDB,
    MYSQLImageObjectDatabaseConnector_bb,
)
from services.DataTypes import ImageObject_bb, Label

# ================================
# Dummy Engine and Connection Classes
# ================================

class DummyConnection:
    def __init__(self):
        self.last_executed = []
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def execute(self, query, params=None):
        # Record the executed query and parameters.
        self.last_executed.append((str(query), params))
        query_str = str(query)
        # For SELECT queries on the image objects table.
        if "FROM ImageObjects_bb" in query_str:
            return DummyResultImageObjects()
        # For SELECT queries on Labels.
        elif "FROM Labels" in query_str:
            return DummyResultLabels()
        # For INSERT queries, simply return None.
        return None

    def commit(self):
        self.committed = True


class DummyResultImageObjects:
    def __init__(self):
        # Simulate a single row for an image object.
        self.rowcount = 1
        # Row layout: (ImageObjectID, ImageID, Class, Confidence, top_left_x, top_left_y, bot_right_x, bot_right_y)
        self.rows = [("io-uuid", "img-uuid", "class-A", 0.95, 10, 20, 30, 40)]
        
    def __iter__(self):
        return iter(self.rows)


class DummyResultLabels:
    def __init__(self):
        # Simulate a single label row.
        # Expected row layout in get_labels:
        # (LabelID, LabellerID, ImageID, <unused>, Class, top_left_x, top_left_y, bot_right_x, bot_right_y, offset_x, offset_y)
        self.rowcount = 1
        self.rows = [("label-id-1", "lab1", "img-uuid", "unused", "label-A", 0, 0, 10, 10, 1, 1)]
        
    def __iter__(self):
        return iter(self.rows)


class DummyEngine:
    def __init__(self):
        self.last_connection = None

    def connect(self):
        conn = DummyConnection()
        self.last_connection = conn
        return conn


# ================================
# Fixtures for Monkeypatching
# ================================

@pytest.fixture
def dummy_engine():
    return DummyEngine()

@pytest.fixture
def patch_create_engine(monkeypatch, dummy_engine):
    """
    Patch the create_engine call in the connector module so it returns our dummy engine.
    """
    import services.ImageObjectDatabaseConnector_bb as iodb
    monkeypatch.setattr(iodb, "create_engine", lambda url: dummy_engine)

@pytest.fixture(autouse=True)
def patch_env_vars(monkeypatch):
    # Set dummy environment variables for database connection.
    monkeypatch.setenv("_LABELDATABASE_MYSQLUSER", "dummy_user")
    monkeypatch.setenv("_LABELDATABASE_MYSQLPASSWORD", "dummy_pass")
    monkeypatch.setenv("_LABELDATABASE_MYSQLHOST", "dummy_host")
    monkeypatch.setenv("_LABELDATABASE_MYSQLDATABASE", "dummy_db")


# ================================
# Tests for the Abstract Base Class and NoneDB
# ================================

def test_abstract_base_instantiation():
    # Instantiating an abstract base class should raise a TypeError.
    with pytest.raises(TypeError):
        ImageObjectDatabaseConnector_bb()

def test_nonedb_methods():
    # NoneDB methods are implemented as pass, so they should return None.
    none_db = NoneDB()
    assert none_db.make_db_connection() is None
    assert none_db.push_imageobject(None) is None
    assert none_db.get_imageobjects("SELECT 1") is None


# ================================
# Tests for MYSQLImageObjectDatabaseConnector_bb
# ================================

@pytest.fixture
def dummy_imageobject():
    """
    Create a dummy ImageObject_bb instance with known values.
    """
    return ImageObject_bb(
        ImageObjectID="io-uuid",
        ImageID="img-uuid",
        Class="class-A",
        Confidence=0.95,
        top_left_x=10,
        top_left_y=20,
        bot_right_x=30,
        bot_right_y=40
    )

def test_push_imageobject(monkeypatch, patch_create_engine, dummy_engine, dummy_imageobject):
    """
    Test that push_imageobject constructs the proper query parameters
    and calls commit on the connection.
    """
    connector = MYSQLImageObjectDatabaseConnector_bb()
    connector.push_imageobject(dummy_imageobject)
    conn = dummy_engine.last_connection
    # Verify that commit was called.
    assert conn.committed is True

    # The dummy connection should have recorded at least one executed query.
    # We check that one of the executed queries matches the INSERT statement.
    executed_queries = [query for query, params in conn.last_executed if "INSERT INTO ImageObjects_bb" in query]
    assert len(executed_queries) > 0

    # Retrieve the parameters used in the INSERT.
    for query, params in conn.last_executed:
        if "INSERT INTO ImageObjects_bb" in query:
            expected_params = {
                "ImageObjectID": dummy_imageobject.ImageObjectID,
                "ImageID": dummy_imageobject.ImageID,
                "Class": dummy_imageobject.Class,
                "Confidence": dummy_imageobject.Confidence,
                "top_left_x": dummy_imageobject.top_left_x,
                "top_left_y": dummy_imageobject.top_left_y,
                "bot_right_x": dummy_imageobject.bot_right_x,
                "bot_right_y": dummy_imageobject.bot_right_y,
            }
            assert params == expected_params
            break

def test_get_imageobjects(monkeypatch, patch_create_engine, dummy_engine):
    """
    Test that get_imageobjects rebuilds an ImageObject_bb instance
    and retrieves associated label(s) correctly.
    """
    connector = MYSQLImageObjectDatabaseConnector_bb()
    # Dummy SELECT query.
    query = "SELECT * FROM ImageObjects_bb WHERE ImageObjectID = 'io-uuid';"
    image_objects = connector.get_imageobjects(query)
    # We expect one image object.
    assert isinstance(image_objects, list)
    assert len(image_objects) == 1
    io_obj = image_objects[0]
    # Check that the fields are set as expected from our dummy result.
    assert io_obj.ImageObjectID == "io-uuid"
    assert io_obj.ImageID == "img-uuid"
    assert io_obj.Class == "class-A"
    assert io_obj.Confidence == 0.95
    assert io_obj.top_left_x == 10
    assert io_obj.top_left_y == 20
    assert io_obj.bot_right_x == 30
    assert io_obj.bot_right_y == 40

def test_get_labels(monkeypatch, patch_create_engine, dummy_engine):
    """
    Test the get_labels helper function separately.
    """
    connector = MYSQLImageObjectDatabaseConnector_bb()
    # Dummy query for labels.
    query = text("""
        SELECT * FROM Labels WHERE LabelID in 
        (SELECT LabelID FROM my_image_db.Labels_ImageObjects WHERE ImageObjectID = :imageobjectid);
    """)
    data = {"imageobjectid": "io-uuid"}
    labels = connector.get_labels(query, data)
    # Verify that a list with one Label is returned.
    assert isinstance(labels, list)
    assert len(labels) == 1
    label_obj = labels[0]
    assert isinstance(label_obj, Label)
    # Check some expected fields from the dummy label row.
    assert label_obj.LabelID == "label-id-1"
    assert label_obj.LabellerID == "lab1"
    assert label_obj.ImageID == "img-uuid"
    assert label_obj.Class == "label-A"
    assert label_obj.top_left_x == 0
    assert label_obj.top_left_y == 0
    assert label_obj.bot_right_x == 10
    assert label_obj.bot_right_y == 10
    assert label_obj.offset_x == 1
    assert label_obj.offset_y == 1
