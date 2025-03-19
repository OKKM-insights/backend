import pytest
from unittest.mock import MagicMock
from sqlalchemy import text

from services.LabelDatabaseConnector import MYSQLLabelDatabaseConnector
from services.DataTypes import Label


@pytest.fixture
def dummy_label_connector():
    """
    Creates an instance of MYSQLLabelDatabaseConnector with a mocked engine
    so we don't connect to a real database.
    """
    connector = MYSQLLabelDatabaseConnector()
    mock_engine = MagicMock()
    mock_connection = MagicMock()
    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_connection
    mock_context.__exit__.return_value = None

    # Override the connector's engine
    connector.cnx = mock_engine
    mock_engine.connect.return_value = mock_context
    return connector


def test_push_label_success(dummy_label_connector):
    """
    Test that push_label executes the correct insert query with the right data.
    """
    mock_connection = dummy_label_connector.cnx.connect.return_value.__enter__.return_value

    label = Label(
        LabelID="label1",
        LabellerID="lab1",
        ImageID="img1",
        Class="dog",
        top_left_x=10,
        top_left_y=20,
        bot_right_x=50,
        bot_right_y=60,
        offset_x=5,
        offset_y=5,
        creation_time="2025-03-10",
        origImageID="orig1"
    )

    dummy_label_connector.push_label(label)

    # push_label should execute exactly one query + commit
    assert mock_connection.execute.call_count == 1
    assert mock_connection.commit.call_count == 1

    # Verify the inserted values
    insert_call = mock_connection.execute.call_args
    (sql_text, ) = insert_call[0]
    # The code in push_label uses f-string with the entire tuple of values
    # We won't parse the entire text string, but we can confirm it includes
    # our LabelID and other fields
    assert "label1" in str(sql_text)
    assert "lab1" in str(sql_text)
    assert "dog" in str(sql_text)
    assert "2025-03-10" in str(sql_text)


def test_get_labels_success(dummy_label_connector):
    """
    Test that get_labels returns a list of Label objects.
    """
    mock_connection = dummy_label_connector.cnx.connect.return_value.__enter__.return_value
    mock_result = MagicMock()
    mock_result.rowcount = 2
    # Return 2 rows
    rows = [
        ("label1", "lab1", "img1", "cat", 0, 0, 10, 10, 0, 0, "2025-03-10", "orig1"),
        ("label2", "lab2", "img2", "dog", 5, 5, 15, 15, 2, 2, "2025-03-11", "orig2"),
    ]
    mock_result.__iter__.return_value = iter(rows)
    mock_connection.execute.return_value = mock_result

    query = "SELECT * FROM Labels;"
    labels = dummy_label_connector.get_labels(query)
    assert len(labels) == 2

    # Check first label
    assert labels[0].LabelID == "label1"
    assert labels[0].Class == "cat"
    assert labels[0].creation_time == "2025-03-10"

    # Check second label
    assert labels[1].LabelID == "label2"
    assert labels[1].Class == "dog"
    assert labels[1].creation_time == "2025-03-11"


def test_get_labels_no_results(dummy_label_connector):
    """
    Test that get_labels returns an empty list when the query returns no rows.
    """
    mock_connection = dummy_label_connector.cnx.connect.return_value.__enter__.return_value
    mock_result = MagicMock()
    mock_result.rowcount = 0
    mock_result.__iter__.return_value = iter([])
    mock_connection.execute.return_value = mock_result

    query = "SELECT * FROM Labels WHERE LabelID='nonexistent';"
    labels = dummy_label_connector.get_labels(query)
    assert labels == []  # Should be empty
