import os
import base64
from flask import Blueprint, request, jsonify
from services.core_img_db_connector import get_db_connection
from mysql.connector import Error
from datetime import date
from PIL import Image
import io

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

        # Insert into Clients or Labellers table based on user_type
        if user_type == 'client':
            name = data.get('company_name')
            industry = data.get('industry')
            typical_projects = data.get('typical_proj')

            client_query = """
            INSERT INTO Clients (email, password, profile_picture, name, industry, typical_projects)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(client_query, (email, password, profile_picture_blob, name, industry, typical_projects))

        elif user_type == 'labeller':
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            skills = data.get('skills')
            availability = data.get('availability')

            labeller_query = """
            INSERT INTO Labellers (email, password, profile_picture, first_name, last_name, skills, availability)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(labeller_query, (email, password, profile_picture_blob, first_name, last_name, skills, availability))

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
    try:
        print(request.form)
        client_id = request.form.get('client-id')
        project_name = request.form.get('project-name')
        project_description = request.form.get('project-description')
        end_date = request.form.get('end-date')
        analysis_goal = request.form.get('analysis-goal')
        image = request.files.get('image-upload')

        if not client_id or not project_name or not end_date or not image:
            return jsonify({'error': 'Missing required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert into Projects table
        project_query = """
            INSERT INTO Projects (clientId, name, description, endDate, categories) 
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(project_query, (client_id, project_name, project_description, end_date, analysis_goal))
        project_id = cursor.lastrowid

        image_data = image.read()
        image_query = """
            INSERT INTO OriginalImages (projectId, image) 
            VALUES (%s, %s)
        """
        cursor.execute(image_query, (project_id, image_data))
        original_image_id = cursor.lastrowid

        # Very rough preprocessing
        img = Image.open(io.BytesIO(image_data))
        img_width, img_height = img.size
        tile_size = 300

        for y_offset in range(0, img_height, tile_size):
            for x_offset in range(0, img_width, tile_size):
                # Ensure we don't go beyond the image boundary
                box = (x_offset, y_offset, min(x_offset + tile_size, img_width), min(y_offset + tile_size, img_height))
                tile = img.crop(box)

                # Convert the tile to a blob (byte data)
                img_byte_arr = io.BytesIO()
                tile.save(img_byte_arr, format='PNG')
                img_blob = img_byte_arr.getvalue()

                # Insert the tile into the Images table
                insert_tile_query = """
                    INSERT INTO Images (project_id, original_image_id, image_width, image_height, x_offset, y_offset, image)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_tile_query, (project_id, original_image_id, tile_size, tile_size, x_offset, y_offset, img_blob))


        conn.commit()

        return jsonify({'message': 'Project created successfully', 'project_id': project_id}), 200

    except Error as e:
        print(str(e))
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@user_project_blueprint.route('/api/login', methods=['POST'])
def login_user():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        user_type = data.get('userType')

        if not email or not password or not user_type:
            return jsonify({'error': 'Email, password, and user_type are required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Determine which table to query based on user_type
        if user_type == 'client':
            query = """
                SELECT id, email, profile_picture, name AS company_name, industry, typical_projects
                FROM Clients
                WHERE email = %s AND password = %s
            """
        elif user_type == 'labeller':
            query = """
                SELECT id, email, profile_picture, first_name, last_name, skills, availability
                FROM Labellers
                WHERE email = %s AND password = %s
            """
        else:
            return jsonify({'error': 'Invalid user_type'}), 400

        cursor.execute(query, (email, password))
        user = cursor.fetchone()

        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401

        user_info = {
            'id': user['id'],
            'email': user['email'], 
            'profile_picture': base64.b64encode(user['profile_picture']).decode('utf-8') if user['profile_picture'] else None
        }

        if user_type == 'client':
            user_info.update({
                'company_name': user['company_name'],
                'industry': user['industry'],
                'typical_projects': user['typical_projects']
            })
        elif user_type == 'labeller':
            user_info.update({
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'skills': user['skills'],
                'availability': user['availability']
            })

        return jsonify({'user': user_info}), 200

    except Error as e:
        print(str(e))
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@user_project_blueprint.route('/api/projects', methods=['GET'])
def get_projects():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        today = date.today()

        query = """
        SELECT projectId AS id, name AS title, description 
        FROM Projects 
        WHERE endDate >= %s
        """
        cursor.execute(query, (today,))
        projects = cursor.fetchall()

        return jsonify({"projects": projects}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@user_project_blueprint.route('/api/getImages', methods=['GET'])
def get_images():
    try:
        # Get query parameters
        project_id = request.args.get('projectId')
        limit = request.args.get('limit', default=10, type=int)
        offset = request.args.get('offset', default=0, type=int)

        if not project_id:
            return jsonify({"error": "Missing projectId parameter"}), 400

        # Convert project_id to an integer (if it's not already)
        project_id = int(project_id)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT *
        FROM Images
        WHERE project_id = %s
        LIMIT %s OFFSET %s
        """
        cursor.execute(query, (project_id, limit, offset))
        images = cursor.fetchall()

        for image in images:
            image['image'] = base64.b64encode(image['image']).decode('utf-8')

        return jsonify({"images": images}), 200

    except Exception as e:
        print(str(e))
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@user_project_blueprint.route('/api/project/<int:project_id>', methods=['GET'])
def get_project_categories(project_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Query to get categories from the Projects table
        query = """
        SELECT categories
        FROM Projects
        WHERE projectId = %s
        """
        cursor.execute(query, (project_id,))
        project = cursor.fetchone()

        if not project:
            return jsonify({"error": "Project not found"}), 404

        # Assuming categories is stored as a comma-separated string
        categories = project['categories']
        return jsonify({"categories": categories}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()