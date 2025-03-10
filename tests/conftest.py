import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from app import create_app

# Ensure backend is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_db():
    with patch("services.core_img_db_connector.get_db_connection") as mock_conn:
        mock_conn.return_value = MagicMock()
        yield mock_conn
