import os
from flask import Blueprint, request, jsonify
from services.core_img_db_connector import get_db_connection
from mysql.connector import Error

user_project_blueprint = Blueprint('user_project_routes', __name__)

@user_project_blueprint.route('/api/register', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        print(data)
        email = data.get('email')
        password = data.get('password')
        user_type = data.get('user_type')

        picture_path = os.path.join(os.getcwd(), 'static/images/default_profile_pic.jpg')
        with open(picture_path, 'rb') as f:
                profile_picture_blob = f.read()

        conn = get_db_connection()
        cursor = conn.cursor()

        user_query = """
            INSERT INTO Users (email, password, profile_picture, user_type)
            VALUES (%s, %s, %s, %s)
            """
        cursor.execute(user_query, (email, password, profile_picture_blob, user_type))
        user_id = cursor.lastrowid

        # Insert into Clients or Labellers table based on user_type
        if user_type == 'client':
            name = data.get('company_name')
            industry = data.get('industry')
            typical_projects = data.get('typical_proj')

            client_query = """
            INSERT INTO Clients (user_id, name, industry, typical_projects)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(client_query, (user_id, name, industry, typical_projects))

        elif user_type == 'labeler':
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            skills = data.get('skills')
            availability = data.get('availability')

            labeller_query = """
            INSERT INTO Labellers (user_id, first_name, last_name, skills, availability)
            VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(labeller_query, (user_id, first_name, last_name, skills, availability))

        # Commit the transaction
        conn.commit()
        return jsonify({'message': 'User registered successfully'}), 200
    except Error as e:
        print(str(e))
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@user_project_blueprint.route('/api/create_project', methods=['POST'])
def create_project():
    data = request.get_json()
    user_id = data.get('user_id')  # Assuming the user ID is provided
    project_name = data.get('project_name')
    description = data.get('description')

    if not (user_id and project_name and description):
        return jsonify({'error': 'Missing required fields'}), 400

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "INSERT INTO projects (user_id, project_name, description) VALUES (%s, %s, %s)",
            (user_id, project_name, description)
        )
        connection.commit()
        return jsonify({'message': 'Project created successfully'}), 201
    except Exception as e:
        connection.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        connection.close()