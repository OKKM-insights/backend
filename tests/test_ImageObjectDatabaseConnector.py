import pytest
from unittest.mock import MagicMock
from sqlalchemy import text

from services.ImageObjectDatabaseConnector import MYSQLImageObjectDatabaseConnector
from services.DataTypes import ImageObject, Label


@pytest.fixture
def dummy_connector():
    """
    Creates an instance of MYSQLImageObjectDatabaseConnector with a mocked engine
    so we don't connect to a real database.
    """
    connector = MYSQLImageObjectDatabaseConnector()
    mock_engine = MagicMock()
    mock_connection = MagicMock()
    mock_context = MagicMock()
    mock_context.__enter__.return_value = mock_connection
    mock_context.__exit__.return_value = None

    # Override the connector's engine
    connector.cnx = mock_engine
    mock_engine.connect.return_value = mock_context
    return connector


def test_push_imageobject_success(dummy_connector):
    """
    Test that push_imageobject executes the correct queries with the right data.
    """
    mock_connection = dummy_connector.cnx.connect.return_value.__enter__.return_value

    # Create a sample ImageObject with related pixels and labels
    label1 = Label(LabelID="label1")
    label2 = Label(LabelID="label2")
    image_object = ImageObject(
        ImageObjectID="obj1",
        ImageID="img1",
        Class="cat",
        Confidence=0.9,
        related_pixels=[[0, 1], [2, 3]],
        related_labels=[label1, label2]
    )

    # Call the method under test
    dummy_connector.push_imageobject(image_object)

    # push_imageobject should execute 1 query for the image object, 
    # plus one for each pixel, plus one for each label => total 1 + 2 + 2 = 5
    assert mock_connection.execute.call_count == 5
    # Also check that commit was called once
    assert mock_connection.commit.call_count == 1

    # Let's verify the first call for inserting the ImageObject
    insert_obj_call = mock_connection.execute.call_args_list[0]
    query, params = insert_obj_call[0]  # The first item in call_args is a tuple (query, params)
    assert isinstance(query, text)      # Should be a SQLAlchemy text object
    assert params["ImageObjectID"] == "obj1"
    assert params["ImageID"] == "img1"
    assert params["Class"] == "cat"
    assert params["Confidence"] == 0.9


def test_get_imageobjects_success(dummy_connector):
    """
    Test that get_imageobjects returns a list of ImageObject objects
    with related pixels and labels.
    """
    # We'll mock the results of the main query (ImageObjects table)
    # Suppose we find 2 image objects in the DB
    rows_main = [
        ("obj1", "img1", "cat", 0.9),
        ("obj2", "img2", "dog", 0.8)
    ]

    # Next, we also need to mock calls to:
    #   1) get_labels() (which calls the query_label_ids inside get_imageobjects)
    #   2) query_pixels (which fetches from Pixels_in_ImageObject)
    # We'll do this by side_effect or sequential calls.

    # For get_labels, the connector calls self.get_labels(query_label_ids, data)
    # We can mock that method directly:
    dummy_connector.get_labels = MagicMock(side_effect=[
        # For obj1, we return 1 label
        [Label(LabelID="label1", Class="cat")],
        # For obj2, we return 2 labels
        [Label(LabelID="label2", Class="dog"), Label(LabelID="label3", Class="dog")]
    ])

    # For pixels, we return a different set for each object
    # We'll intercept the calls to connection.execute(...) 
    # to see if the "query_pixels" text is used, then return our data.
    def mock_execute_side_effect(query, data=None):
        if "FROM ImageObjects" in str(query):
            # This is the main get_imageobjects query
            mock_result = MagicMock()
            mock_result.rowcount = len(rows_main)
            mock_result.__iter__.return_value = iter(rows_main)
            return mock_result
        elif "FROM Pixels_in_ImageObject" in str(query):
            # This is the query for pixels
            if data["imageobjectid"] == "obj1":
                pixels = [(10, 20), (30, 40)]
            else:
                pixels = [(5, 5)]
            mock_result = MagicMock()
            mock_result.rowcount = len(pixels)
            mock_result.__iter__.return_value = iter(pixels)
            return mock_result
        return None

    mock_connection = dummy_connector.cnx.connect.return_value.__enter__.return_value
    mock_connection.execute.side_effect = mock_execute_side_effect

    # Call get_imageobjects
    query = "SELECT * FROM ImageObjects;"
    result_objects = dummy_connector.get_imageobjects(query)

    # We expect 2 objects
    assert len(result_objects) == 2
    # First object
    assert result_objects[0].ImageObjectID == "obj1"
    assert result_objects[0].ImageID == "img1"
    assert result_objects[0].Class == "cat"
    assert result_objects[0].Confidence == 0.9
    # Should have 2 pixels from our mock
    assert result_objects[0].related_pixels == [[10, 20], [30, 40]]
    # 1 label from our side_effect
    assert len(result_objects[0].related_labels) == 1
    assert result_objects[0].related_labels[0].LabelID == "label1"

    # Second object
    assert result_objects[1].ImageObjectID == "obj2"
    assert result_objects[1].ImageID == "img2"
    assert result_objects[1].Class == "dog"
    assert result_objects[1].Confidence == 0.8
    # 1 pixel
    assert result_objects[1].related_pixels == [[5, 5]]
    # 2 labels
    assert len(result_objects[1].related_labels) == 2
    assert result_objects[1].related_labels[0].LabelID == "label2"
    assert result_objects[1].related_labels[1].LabelID == "label3"


def test_get_imageobjects_no_results(dummy_connector):
    """
    Test that get_imageobjects returns an empty list when no rows are found.
    """
    mock_connection = dummy_connector.cnx.connect.return_value.__enter__.return_value
    mock_result = MagicMock()
    mock_result.rowcount = 0
    mock_result.__iter__.return_value = iter([])
    mock_connection.execute.return_value = mock_result

    query = "SELECT * FROM ImageObjects WHERE ImageID='nonexistent';"
    result_objects = dummy_connector.get_imageobjects(query)
    assert result_objects == []  # Should be an empty list
