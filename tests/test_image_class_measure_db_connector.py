import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import text

from services.ImageClassMeasureDatabaseConnector import MYSQLImageClassMeasureDatabaseConnector
from services.DataTypes import ImageClassMeasure

# Fixture to create a dummy MYSQL connector with a mocked engine connection
@pytest.fixture
def dummy_connector():
    # Create an instance; we will override its cnx attribute to avoid an actual DB connection.
    connector = MYSQLImageClassMeasureDatabaseConnector()
    # Create a dummy connection context manager
    dummy_conn = MagicMock()
    dummy_context = MagicMock()
    dummy_context.__enter__.return_value = dummy_conn
    dummy_context.__exit__.return_value = None
    # Override the connector's engine so that connect() returns our dummy context manager
    connector.cnx = MagicMock()
    connector.cnx.connect.return_value = dummy_context
    return connector

# ----------------- Tests for push_imageclassmeasure -----------------
def test_push_imageclassmeasure_success(dummy_connector):
    # Create a small ImageClassMeasure object.
    # Note: push_imageclassmeasure indexes likelihoods/confidence/helper_values as [x][y],
    # so we provide matrices with dimensions: im_width x im_height.
    # For a 2x2 image: im_width=2, im_height=2.
    likelihoods = [
        [0.7, 0.9],  # Column 0: row0, row1
        [0.8, 1.0]   # Column 1: row0, row1
    ]
    confidence = [
        [0.1, 0.3],
        [0.2, 0.4]
    ]
    helper_values = [
        [[0.6, 0.4], [0.8, 0.2]],  # For column 0
        [[0.7, 0.3], [0.9, 0.1]]   # For column 1
    ]
    icm = ImageClassMeasure(
        imageID="test",
        likelihoods=likelihoods,
        confidence=confidence,
        helper_values=helper_values,
        label="test_label",
        im_width=2,
        im_height=2
    )

    dummy_conn = dummy_connector.cnx.connect.return_value.__enter__.return_value

    # Call the method under test.
    dummy_connector.push_imageclassmeasure(icm)

    # Check that execute was called once.
    assert dummy_conn.execute.call_count == 1

    # Retrieve the batch data passed to execute.
    call_args = dummy_conn.execute.call_args
    # The call should have been: execute(query, batch_data)
    _, kwargs = call_args
    # The batch data is the second positional argument; if provided as positional args,
    # then it is in call_args[0][1]
    batch_data = call_args[0][1]
    # For a 2x2 image, we expect 4 rows of data.
    assert len(batch_data) == 4

    # Verify one of the rows: Order of iteration in push:
    # for y in range(im_height): for x in range(im_width):
    # So first row: y=0, x=0: expect likelihood = likelihoods[0][0], confidence = confidence[0][0]
    first_row = batch_data[0]
    assert first_row["ImageID"] == "test"
    assert first_row["x"] == 0
    assert first_row["y"] == 0
    assert first_row["label"] == "test_label"
    assert first_row["likelihood"] == 0.7
    assert first_row["confidence"] == 0.1
    assert first_row["helpervalue_1"] == 0.6
    assert first_row["helpervalue_2"] == 0.4
    assert first_row["im_height"] == 2
    assert first_row["im_width"] == 2

    # Also ensure commit was called.
    assert dummy_conn.commit.call_count == 1

# ----------------- Tests for get_imageclassmeasures -----------------
class DummyResult:
    def __init__(self, rows):
        self._rows = rows
        self.rowcount = len(rows)

    def __iter__(self):
        return iter(self._rows)

def test_get_imageclassmeasures_success(dummy_connector):
    # Prepare 4 rows for a 2x2 image.
    # Each row is: (ImageID, x, y, label, likelihood, confidence, helpervalue_1, helpervalue_2, im_height, im_width)
    rows = [
        ("test", 0, 0, "test_label", 0.7, 0.1, 0.6, 0.4, 2, 2),
        ("test", 1, 0, "test_label", 0.8, 0.2, 0.7, 0.3, 2, 2),
        ("test", 0, 1, "test_label", 0.9, 0.3, 0.8, 0.2, 2, 2),
        ("test", 1, 1, "test_label", 1.0, 0.4, 0.9, 0.1, 2, 2)
    ]
    dummy_result = DummyResult(rows)

    dummy_conn = dummy_connector.cnx.connect.return_value.__enter__.return_value
    dummy_conn.execute.return_value = dummy_result

    # Call get_imageclassmeasures with a dummy query.
    query = "SELECT * FROM ImageClassMeasure WHERE ImageID = 'test' AND label = 'test_label';"
    icm = dummy_connector.get_imageclassmeasures(query)

    # Verify that the connector reconnected.
    assert dummy_conn.execute.call_count >= 1

    # Check that the returned ImageClassMeasure has correctly ordered matrices.
    # According to the code, ordering is done with indices: likelihoods_ordered[y][x]
    expected_likelihoods = [
        [0.7, 0.8],  # Row 0: x=0 then x=1
        [0.9, 1.0]   # Row 1: x=0 then x=1
    ]
    expected_confidence = [
        [0.1, 0.2],
        [0.3, 0.4]
    ]
    expected_helper_values = [
        [[0.6, 0.4], [0.7, 0.3]],
        [[0.8, 0.2], [0.9, 0.1]]
    ]

    assert icm.imageID == "test"
    assert icm.label == "test_label"
    assert icm.im_height == 2
    assert icm.im_width == 2
    assert icm.likelihoods == expected_likelihoods
    assert icm.confidence == expected_confidence
    assert icm.helper_values == expected_helper_values

def test_get_imageclassmeasures_no_results(dummy_connector):
    # Simulate a result with no rows.
    dummy_result = DummyResult([])
    dummy_conn = dummy_connector.cnx.connect.return_value.__enter__.return_value
    dummy_conn.execute.return_value = dummy_result

    query = "SELECT * FROM ImageClassMeasure WHERE ImageID = 'nonexistent';"
    icm = dummy_connector.get_imageclassmeasures(query)
    # When no rows are found, the method should return None.
    assert icm is None
