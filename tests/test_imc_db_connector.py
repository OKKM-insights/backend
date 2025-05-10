import os
import sys
import uuid
import numpy as np
import pytest
from sqlalchemy import text
from dotenv import load_dotenv

# Import the connector classes and types using absolute imports.
from services.ImageClassMeasureDatabaseConnector import (
    ImageClassMeasureDatabaseConnector,
    NoneDB,
    MYSQLImageClassMeasureDatabaseConnector,
)
from services.DataTypes import ImageClassMeasure, Label

# ================================
# Dummy Engine and Connection Classes
# ================================

class DummyConnection:
    def __init__(self):
        self.executed_query = None
        self.executed_params = None
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def execute(self, query, params=None):
        self.executed_query = query
        self.executed_params = params
        # When a SELECT query is issued, return a dummy result.
        if "SELECT" in str(query):
            # Default dummy result for get_imageclassmeasures (expects several rows)
            return DummyResult()
        return None

    def commit(self):
        self.committed = True


class DummyResult:
    def __init__(self):
        # For get_imageclassmeasures: simulate a 2x2 grid.
        self.rowcount = 4
        # The rows are ordered as pushed by push_imageclassmeasure.
        # Each row: (ImageID, x, y, label, likelihood, confidence, helpervalue_1, helpervalue_2, im_height, im_width)
        self.rows = [
            ("test", 0, 0, "label", 0.1, 0.2, 0.3, 0.4, 2, 2),
            ("test", 1, 0, "label", 0.11, 0.21, 0.31, 0.41, 2, 2),
            ("test", 0, 1, "label", 0.12, 0.22, 0.32, 0.42, 2, 2),
            ("test", 1, 1, "label", 0.13, 0.23, 0.33, 0.43, 2, 2),
        ]

    def __iter__(self):
        return iter(self.rows)


# A dummy engine whose connect() returns a DummyConnection.
class DummyEngine:
    def __init__(self):
        self.last_connection = None

    def connect(self):
        conn = DummyConnection()
        self.last_connection = conn
        return conn


# For get_imageclassmeasures_images we need a different dummy result.
class DummyResultImages:
    def __init__(self):
        self.rowcount = 1
        im_height = 2
        im_width = 2
        likelihood_arr = np.array([[0.1, 0.11], [0.12, 0.13]], dtype=np.float16)
        confidence_arr = np.array([[0.2, 0.21], [0.22, 0.23]], dtype=np.float16)
        helper1_arr = np.array([[0.3, 0.31], [0.32, 0.33]], dtype=np.float16)
        helper2_arr = np.array([[0.4, 0.41], [0.42, 0.43]], dtype=np.float16)
        self.row = (
            "test_images",
            "label",
            likelihood_arr.tobytes(),
            confidence_arr.tobytes(),
            helper1_arr.tobytes(),
            helper2_arr.tobytes(),
            im_height,
            im_width,
        )

    def __iter__(self):
        return iter([self.row])


# ================================
# Fixtures for Monkeypatching
# ================================

@pytest.fixture
def dummy_engine():
    return DummyEngine()

@pytest.fixture
def patch_create_engine(monkeypatch, dummy_engine):
    """
    Patch the create_engine used in the connector module to return our dummy engine.
    """
    # The module's namespace where create_engine is used is "services.ImageClassMeasureDatabaseConnector"
    import services.ImageClassMeasureDatabaseConnector as icmdc

    monkeypatch.setattr(icmdc, "create_engine", lambda url: dummy_engine)


@pytest.fixture(autouse=True)
def patch_env_vars(monkeypatch):
    # Set dummy environment variables so that make_db_connection() works.
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
        ImageClassMeasureDatabaseConnector()


def test_nonedb_methods():
    # NoneDB implements methods as pass so they should do nothing.
    none_db = NoneDB()
    # They simply return None.
    assert none_db.make_db_connection() is None
    assert none_db.push_imageclassmeasure(None) is None
    assert none_db.get_imageclassmeasures("SELECT 1") is None


# ================================
# Tests for MYSQLImageClassMeasureDatabaseConnector
# ================================

@pytest.fixture
def dummy_imageclassmeasure():
    """
    Create a dummy ImageClassMeasure with a 2x2 grid.
    Note: The code in push_imageclassmeasure indexes arrays as [x][y],
    so we define the arrays with length=im_width at the first level.
    """
    im_width = 2
    im_height = 2
    likelihoods = [
        [0.1, 0.12],  # For x=0: y=0, y=1
        [0.11, 0.13]  # For x=1: y=0, y=1
    ]
    confidence = [
        [0.2, 0.22],
        [0.21, 0.23]
    ]
    helper_values = [
        [[0.3, 0.31], [0.32, 0.33]],
        [[0.4, 0.41], [0.42, 0.43]]
    ]
    return ImageClassMeasure(
        imageID="test",
        likelihoods=likelihoods,
        confidence=confidence,
        helper_values=helper_values,
        label="label",
        im_width=im_width,
        im_height=im_height
    )


def test_push_imageclassmeasure(monkeypatch, patch_create_engine, dummy_engine, dummy_imageclassmeasure):
    """
    Test that push_imageclassmeasure constructs the batch data correctly
    and calls commit on the connection.
    """
    # Instantiate the connector; __init__ calls make_db_connection()
    connector = MYSQLImageClassMeasureDatabaseConnector()
    # Call push_imageclassmeasure with our dummy object.
    connector.push_imageclassmeasure(dummy_imageclassmeasure)

    # Retrieve the dummy connection used.
    conn = dummy_engine.last_connection
    # Verify that commit was called.
    assert conn.committed is True

    # Expected batch_data length: im_height * im_width = 4
    expected_length = dummy_imageclassmeasure.im_height * dummy_imageclassmeasure.im_width
    assert isinstance(conn.executed_params, list)
    assert len(conn.executed_params) == expected_length

    # Check one sample: for y=0, x=0 we expect values from arrays at index [0][0]
    expected_dict = {
        "ImageID": "test",
        "x": 0,
        "y": 0,
        "label": "label",
        "likelihood": dummy_imageclassmeasure.likelihoods[0][0],
        "confidence": dummy_imageclassmeasure.confidence[0][0],
        "helpervalue_1": dummy_imageclassmeasure.helper_values[0][0][0],
        "helpervalue_2": dummy_imageclassmeasure.helper_values[0][0][1],
        "im_height": dummy_imageclassmeasure.im_height,
        "im_width": dummy_imageclassmeasure.im_width,
    }
    assert conn.executed_params[0] == expected_dict


def test_push_imageclassmeasure_images(monkeypatch, patch_create_engine, dummy_engine, dummy_imageclassmeasure):
    """
    Test that push_imageclassmeasure_images correctly converts arrays to binary
    and calls commit.
    """
    # Instantiate the connector.
    connector = MYSQLImageClassMeasureDatabaseConnector()
    connector.push_imageclassmeasure_images(dummy_imageclassmeasure)

    conn = dummy_engine.last_connection
    assert conn.committed is True

    # Build the expected data dictionary.
    helper_values_1 = [[pixel[0] for pixel in row] for row in dummy_imageclassmeasure.helper_values]
    helper_values_2 = [[pixel[1] for pixel in row] for row in dummy_imageclassmeasure.helper_values]

    expected_data = {
        "ImageID": dummy_imageclassmeasure.imageID,
        "label": dummy_imageclassmeasure.label,
        "likelihood": np.array(dummy_imageclassmeasure.likelihoods, dtype=np.float16).tobytes(),
        "confidence": np.array(dummy_imageclassmeasure.confidence, dtype=np.float16).tobytes(),
        "helpervalue_1": np.array(helper_values_1, dtype=np.float16).tobytes(),
        "helpervalue_2": np.array(helper_values_2, dtype=np.float16).tobytes(),
        "im_height": dummy_imageclassmeasure.im_height,
        "im_width": dummy_imageclassmeasure.im_width,
    }
    # Compare the bytes and other values.
    executed = conn.executed_params
    # executed is a dict; compare keys and values.
    for key in expected_data:
        assert executed[key] == expected_data[key]


def test_get_imageclassmeasures(monkeypatch, patch_create_engine, dummy_engine):
    """
    Test that get_imageclassmeasures correctly rebuilds an ImageClassMeasure from the dummy result.
    """
    connector = MYSQLImageClassMeasureDatabaseConnector()
    # Execute a dummy SELECT query.
    icm = connector.get_imageclassmeasures("SELECT * FROM ImageClassMeasure WHERE ImageID = 'test';")
    # Verify that an object is returned.
    assert isinstance(icm, ImageClassMeasure)
    # Expected ordering based on DummyResult:
    # From rows: x: [0,1,0,1] and y: [0,0,1,1]
    expected_likelihoods = [
        [0.1, 0.11],
        [0.12, 0.13]
    ]
    expected_confidence = [
        [0.2, 0.21],
        [0.22, 0.23]
    ]
    expected_helper_values = [
        [[0.3, 0.4], [0.31, 0.41]],
        [[0.32, 0.42], [0.33, 0.43]]
    ]
    assert icm.imageID == "test"
    assert icm.label == "label"
    assert icm.im_width == 2
    assert icm.im_height == 2
    assert icm.likelihoods == expected_likelihoods
    assert icm.confidence == expected_confidence
    assert icm.helper_values == expected_helper_values


def test_get_imageclassmeasures_images(monkeypatch, patch_create_engine, dummy_engine):
    """
    Test that get_imageclassmeasures_images correctly decodes binary image data.
    """
    # We need to override the DummyConnection.execute method to return a different dummy result.
    def execute_override(query, params=None):
        return DummyResultImages()

    # Patch the connection on the dummy engine.
    original_connect = dummy_engine.connect
    def connect_override():
        conn = original_connect()
        conn.execute = execute_override
        return conn
    monkeypatch.setattr(dummy_engine, "connect", connect_override)

    connector = MYSQLImageClassMeasureDatabaseConnector()
    icm = connector.get_imageclassmeasures_images("SELECT * FROM ImageClassMeasure_images WHERE ImageID = 'test_images';")
    # Verify that an object is returned.
    assert isinstance(icm, ImageClassMeasure)
    # For likelihood and confidence, the arrays were stored as (im_height, im_width, 1)
    expected_likelihoods = np.frombuffer(
        np.array([[0.1, 0.11], [0.12, 0.13]], dtype=np.float16).tobytes(),
        dtype=np.float16
    ).reshape((2, 2, 1)).tolist()
    expected_confidence = np.frombuffer(
        np.array([[0.2, 0.21], [0.22, 0.23]], dtype=np.float16).tobytes(),
        dtype=np.float16
    ).reshape((2, 2, 1)).tolist()
    # For helper values, note the stacking and reshaping in the method.
    helper1 = np.array([[0.3, 0.31], [0.32, 0.33]], dtype=np.float16)
    helper2 = np.array([[0.4, 0.41], [0.42, 0.43]], dtype=np.float16)
    expected_helper_values = np.stack((helper1, helper2), axis=-1).tolist()

    assert icm.imageID == "test_images"
    assert icm.label == "label"
    assert icm.im_height == 2
    assert icm.im_width == 2
    assert icm.likelihoods == expected_likelihoods
    assert icm.confidence == expected_confidence
    assert icm.helper_values == expected_helper_values
