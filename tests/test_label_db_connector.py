import os
import pytest
import urllib.parse
from sqlalchemy import text

# Import the connector classes using absolute imports.
from services.LabelDatabaseConnector import (
    LabelDatabaseConnector,
    NoneDB,
    MYSQLLabelDatabaseConnector,
)
from services.DataTypes import Label

# ================================
# Dummy Engine and Connection Classes
# ================================

class DummyConnection:
    def __init__(self):
        self.last_executed = []  # Store executed queries and parameters.
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def execute(self, query, params=None):
        # Record the executed query and parameters.
        self.last_executed.append((str(query), params))
        query_str = str(query)
        # For SELECT queries, return a dummy result.
        if "SELECT" in query_str:
            return DummyResultLabels()
        return None

    def commit(self):
        self.committed = True

class DummyResultLabels:
    """
    Dummy result for get_labels.
    Expected row layout:
    (LabelID, LabellerID, ImageID, Class, top_left_x, top_left_y, bot_right_x, bot_right_y, offset_x, offset_y, creation_time, origImageID)
    """
    def __init__(self):
        self.rowcount = 1
        self.rows = [
            ("label-uuid", "lab1", "img1", "class-X", 0, 0, 10, 10, 1, 1, "2023-01-01", "orig-img")
        ]

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
    import services.LabelDatabaseConnector as ldc
    monkeypatch.setattr(ldc, "create_engine", lambda url: dummy_engine)

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
        LabelDatabaseConnector()

def test_nonedb_methods():
    none_db = NoneDB()
    # Methods implemented as pass should return None.
    assert none_db.make_db_connection() is None
    assert none_db.push_label(None) is None
    assert none_db.get_labels("SELECT 1") is None

# ================================
# Tests for MYSQLLabelDatabaseConnector
# ================================

def test_push_label(monkeypatch, patch_create_engine, dummy_engine):
    connector = MYSQLLabelDatabaseConnector()
    test_label = Label(
        LabelID="label-uuid",
        LabellerID="lab1",
        ImageID="img1",
        Class="class-X",
        top_left_x=0,
        top_left_y=0,
        bot_right_x=10,
        bot_right_y=10,
        offset_x=1,
        offset_y=1,
        creation_time="2023-01-01",
        origImageID="orig-img"
    )
    connector.push_label(test_label)
    conn = dummy_engine.last_connection
    # Ensure commit was called.
    assert conn.committed is True
    # Check that at least one query was executed containing the INSERT statement.
    insert_queries = [q for q, params in conn.last_executed if "INSERT INTO" in q]
    assert len(insert_queries) > 0
    # Optionally, verify that the query string contains expected label values.
    query_text = insert_queries[0]
    assert "label-uuid" in query_text
    assert "lab1" in query_text
    assert "img1" in query_text
    assert "class-X" in query_text

def test_push_labels_batch(monkeypatch, patch_create_engine, dummy_engine):
    connector = MYSQLLabelDatabaseConnector()
    labels_batch = [{
        "LabelID": "label-uuid",
        "LabellerID": "lab1",
        "ImageID": "img1",
        "Class": "class-X",
        "top_left_x": 0,
        "top_left_y": 0,
        "bot_right_x": 10,
        "bot_right_y": 10,
        "offset_x": 1,
        "offset_y": 1,
        "creation_time": "2023-01-01",
        "origImageID": "orig-img"
    }]
    connector.push_labels_batch(labels_batch)
    conn = dummy_engine.last_connection
    assert conn.committed is True
    # Check that the batch INSERT query was executed with the provided parameters.
    batch_queries = [
        (q, params)
        for q, params in conn.last_executed
        if "INSERT INTO Labels" in q and params == labels_batch
    ]
    assert len(batch_queries) > 0

def test_get_labels(monkeypatch, patch_create_engine, dummy_engine):
    connector = MYSQLLabelDatabaseConnector()
    query = "SELECT * FROM Labels WHERE LabelID = 'label-uuid';"
    labels = connector.get_labels(query)
    # Verify that a list with one Label is returned.
    assert isinstance(labels, list)
    assert len(labels) == 1
    label_obj = labels[0]
    assert label_obj.LabelID == "label-uuid"
    assert label_obj.LabellerID == "lab1"
    assert label_obj.ImageID == "img1"
    assert label_obj.Class == "class-X"
    assert label_obj.top_left_x == 0
    assert label_obj.top_left_y == 0
    assert label_obj.bot_right_x == 10
    assert label_obj.bot_right_y == 10
    assert label_obj.offset_x == 1
    assert label_obj.offset_y == 1
    assert label_obj.creation_time == "2023-01-01"
    assert label_obj.origImageID == "orig-img"
