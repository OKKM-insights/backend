import pytest
from unittest.mock import MagicMock
from sqlalchemy import text

from services.LabellerDatabaseConnector import MYSQLLabellerDatabaseConnector
from services.DataTypes import Labeller


@pytest.fixture
def dummy_labeller_connector():
    """
    Creates an instance of MYSQLLabellerDatabaseConnector with a mocked engine
    so we don't connect to a real database.
    """
    connector = MYSQLLabellerDatabaseConnector()
    mock_engine = MagicMock()
    mock_connection = MagicMock()
    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_connection
    mock_context.__exit__.return_value = None

    # Override the connector's engine
    connector.cnx = mock_engine
    mock_engine.connect.return_value = mock_context
    return connector


def test_push_labeller_success(dummy_labeller_connector):
    """
    Test that push_labeller executes the correct insert query with the right data.
    """
    mock_connection = dummy_labeller_connector.cnx.connect.return_value.__enter__.return_value

    labeller = Labeller(LabellerID="lab1", skill="novice", alpha=2.5, beta=3.5)
    dummy_labeller_connector.push_labeller(labeller)

    # push_labeller should execute exactly one query + commit
    assert mock_connection.execute.call_count == 1
    assert mock_connection.commit.call_count == 1

    insert_call = mock_connection.execute.call_args
    (sql_text, params) = insert_call[0]
    assert isinstance(sql_text, text)
    assert params["labeller_id"] == "lab1"
    assert params["skill"] == "novice"
    assert params["alpha"] == 2.5
    assert params["beta"] == 3.5


def test_get_labellers_success(dummy_labeller_connector):
    """
    Test that get_labellers returns a list of Labeller objects.
    """
    mock_connection = dummy_labeller_connector.cnx.connect.return_value.__enter__.return_value
    mock_result = MagicMock()
    mock_result.rowcount = 2
    rows = [
        ("lab1", "expert", 1.2, 1.0),
        ("lab2", "novice", 2.5, 3.5)
    ]
    mock_result.__iter__.return_value = iter(rows)
    mock_connection.execute.return_value = mock_result

    query = "SELECT * FROM Labeller_skills;"
    labellers = dummy_labeller_connector.get_labellers(query)
    assert len(labellers) == 2

    assert labellers[0].LabellerID == "lab1"
    assert labellers[0].skill == "expert"
    assert labellers[0].alpha == 1.2
    assert labellers[0].beta == 1.0

    assert labellers[1].LabellerID == "lab2"
    assert labellers[1].skill == "novice"
    assert labellers[1].alpha == 2.5
    assert labellers[1].beta == 3.5


def test_get_labellers_no_results(dummy_labeller_connector):
    """
    Test that get_labellers returns an empty list when the query returns no rows.
    """
    mock_connection = dummy_labeller_connector.cnx.connect.return_value.__enter__.return_value
    mock_result = MagicMock()
    mock_result.rowcount = 0
    mock_result.__iter__.return_value = iter([])
    mock_connection.execute.return_value = mock_result

    query = "SELECT * FROM Labeller_skills WHERE Labeller_id='nonexistent';"
    labellers = dummy_labeller_connector.get_labellers(query)
    assert labellers == []


def test_get_labellers_with_data_success(dummy_labeller_connector):
    """
    Test that get_labellers_with_data can execute a parameterized query 
    and returns matching Labeller objects.
    """
    mock_connection = dummy_labeller_connector.cnx.connect.return_value.__enter__.return_value
    mock_result = MagicMock()
    mock_result.rowcount = 1
    rows = [
        ("lab3", "advanced", 3.0, 4.0),
    ]
    mock_result.__iter__.return_value = iter(rows)
    mock_connection.execute.return_value = mock_result

    query = "SELECT * FROM Labeller_skills WHERE skill=:skill"
    data = {"skill": "advanced"}
    labellers = dummy_labeller_connector.get_labellers_with_data(query, data)
    assert len(labellers) == 1
    assert labellers[0].LabellerID == "lab3"
    assert labellers[0].skill == "advanced"
    assert labellers[0].alpha == 3.0
    assert labellers[0].beta == 4.0


def test_get_labellers_with_data_no_results(dummy_labeller_connector):
    """
    Test that get_labellers_with_data returns an empty list for no matching rows.
    """
    mock_connection = dummy_labeller_connector.cnx.connect.return_value.__enter__.return_value
    mock_result = MagicMock()
    mock_result.rowcount = 0
    mock_result.__iter__.return_value = iter([])
    mock_connection.execute.return_value = mock_result

    query = "SELECT * FROM Labeller_skills WHERE skill=:skill"
    data = {"skill": "does_not_exist"}
    labellers = dummy_labeller_connector.get_labellers_with_data(query, data)
    assert labellers == []
