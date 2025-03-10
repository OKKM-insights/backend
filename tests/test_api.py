import json
import base64
from unittest.mock import MagicMock
from api.account_routes import user_project_blueprint

# Register the Blueprint for testing
def test_register_blueprint(client):
    assert "user_project_routes" in client.application.blueprints


# --------------- TEST USER REGISTRATION ---------------
def test_register_user_success(client, mock_db):
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    # Simulate that no duplicate entry exists
    mock_cursor.execute.side_effect = None  # Remove error on insert
    mock_cursor.fetchone.return_value = None  # No existing user

    payload = {
        "email": "unique@example.com",  # Use a unique email to avoid duplicate entry error
        "password": "securepassword",
        "user_type": "client",
        "company_name": "TechCorp",
        "industry": "AI",
        "typical_proj": "Image Classification"
    }

    response = client.post('/api/register', json=payload)
    assert response.status_code == 200  # Should pass
    assert response.json["message"] == "User registered successfully"


def test_register_user_missing_data(client):
    payload = {"email": "unique2@example.com", "password": "12345"}  # Missing user_type field
    response = client.post('/api/register', json=payload)
    # Expecting a 400 BAD REQUEST if the API validates required fields
    assert response.status_code == 400  
    assert "error" in response.json  # Ensure an error message is returned


# --------------- TEST USER LOGIN ---------------
def test_login_user_success(client, mock_db):
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    hashed_pw = base64.b64encode(b"securepassword").decode('utf-8')

    mock_cursor.fetchone.return_value = {
        "id": 1,
        "email": "test@example.com",
        "password": hashed_pw,
        "profile_picture": None
    }

    payload = {"email": "test@example.com", "password": "securepassword", "userType": "client"}
    response = client.post('/api/login', json=payload)

    assert response.status_code == 200
    assert response.json["user"]["email"] == "test@example.com"


def test_login_user_invalid(client, mock_db):
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = None  # No user found

    payload = {"email": "wrong@example.com", "password": "wrongpass", "userType": "client"}
    response = client.post('/api/login', json=payload)
    assert response.status_code == 401
    assert response.json["error"] == "Invalid credentials"


# --------------- TEST PROJECT CREATION ---------------
def test_create_project_success(client, mock_db):
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.lastrowid = 1  # Simulate successful insert

    payload = {
        "client-id": "1",
        "project-name": "New AI Project",
        "project-description": "A new project for AI labeling",
        "end-date": "2025-12-31",
        "analysis-goal": "Object Detection",
    }

    response = client.post('/api/create_project', data=payload, content_type='multipart/form-data')
    assert response.status_code == 200
    assert response.json["message"] == "Project created successfully"


def test_create_project_missing_fields(client):
    payload = {"client-id": "1"}  # Missing required fields
    response = client.post('/api/create_project', data=payload, content_type='multipart/form-data')
    assert response.status_code == 400
    assert response.json["error"] == "Missing required fields"


# --------------- TEST FETCHING PROJECTS ---------------
def test_get_projects_success(client, mock_db):
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    # Return expected project with the title matching the API response
    mock_cursor.fetchall.return_value = [{"id": 1, "title": "Airport Project", "description": "AI work"}]

    response = client.get('/api/projects?userId=1')
    assert response.status_code == 200
    assert response.json["projects"][0]["title"] == "Airport Project"


def test_get_projects_no_user_id(client):
    response = client.get('/api/projects')
    assert response.status_code == 400
    assert response.json["error"] == "Missing userId parameter"


# --------------- TEST FETCHING IMAGES ---------------
def test_get_images_success(client, mock_db):
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    mock_cursor.fetchall.return_value = [{"id": 1, "image": base64.b64encode(b"fakeimage").decode('utf-8')}]

    response = client.get('/api/getImages?projectId=1&userId=1')
    assert response.status_code == 200
    assert "images" in response.json


def test_get_images_missing_params(client):
    response = client.get('/api/getImages')
    assert response.status_code == 400
    assert response.json["error"] == "Missing projectId or userId parameter"


# --------------- TEST UPDATING USER ---------------
def test_update_user_success(client, mock_db):
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_db.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    payload = {
        "email": "updated@example.com",
        "userType": "client",
        "name": "Updated Name",
        "industry": "Updated Industry",
        "typicalProj": "Updated Projects"
    }

    response = client.put('/api/update-user/1', json=payload)
    assert response.status_code == 200
    assert response.json["message"] == "User updated successfully"


def test_update_user_missing_data(client):
    payload = {}  # Missing required fields
    response = client.put('/api/update-user/1', json=payload)
    assert response.status_code == 500  # Should fail due to missing data
