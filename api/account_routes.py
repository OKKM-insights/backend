import os
import base64
import bcrypt
from flask import Blueprint, request, jsonify, send_file
from services.core_img_db_connector import get_db_connection
from utils.ImagePreprocess import preprocess_image, store_tiles
from mysql.connector import Error
from datetime import date
from PIL import Image
import io
import numpy as np

user_project_blueprint = Blueprint('user_project_routes', __name__)

@user_project_blueprint.route('/api/register', methods=['POST'])
def register_user():
    conn = None
    cursor = None
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        user_type = data.get('user_type')

        picture_path = os.path.join(os.getcwd(), 'static/images/default_profile_pic.jpg')
        with open(picture_path, 'rb') as f:
                profile_picture_blob = f.read()

        conn = get_db_connection()
        cursor = conn.cursor()

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        # Insert into Clients or Labellers table based on user_type
        if user_type == 'client':
            name = data.get('company_name')
            industry = data.get('industry')
            typical_projects = data.get('typical_proj')

            client_query = """
            INSERT INTO Clients (email, password, profile_picture, name, industry, typical_projects)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(client_query, (email, hashed_password, profile_picture_blob, name, industry, typical_projects))

        elif user_type == 'labeller':
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            skills = data.get('skills')
            availability = data.get('availability')

            labeller_query = """
            INSERT INTO Labellers (email, password, profile_picture, first_name, last_name, skills, availability)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(labeller_query, (email, hashed_password, profile_picture_blob, first_name, last_name, skills, availability))

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
    conn = None
    cursor = None
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


        img = Image.open(io.BytesIO(image_data))
        image_np = np.array(img)

        # Partition the image into tiles
        tiles = preprocess_image(image_np)

        # Store the tiles in the database
        store_tiles(tiles, project_id, original_image_id, cursor)

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
    conn = None
    cursor = None
    try:
        data = request.get_json()
        print(data)
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
                SELECT id, email, password, profile_picture, name AS company_name, industry, typical_projects
                FROM Clients
                WHERE email = %s
            """
        elif user_type == 'labeller':
            query = """
                SELECT id, email, password, profile_picture, first_name, last_name, skills, availability
                FROM Labellers
                WHERE email = %s
            """
        else:
            return jsonify({'error': 'Invalid user_type'}), 400

        cursor.execute(query, (email,))
        user = cursor.fetchone()

        if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return jsonify({'error': 'Invalid credentials'}), 401

        user_info = {
            'id': user['id'],
            'email': user['email'], 
            'profilePicture': base64.b64encode(user['profile_picture']).decode('utf-8') if user['profile_picture'] else None
        }

        if user_type == 'client':
            user_info.update({
                'name': user['company_name'],
                'industry': user['industry'],
                'typicalProj': user['typical_projects']
            })
        elif user_type == 'labeller':
            user_info.update({
                'firstName': user['first_name'],
                'lastName': user['last_name'],
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
    conn = None
    cursor = None
    try:
        user_id = request.args.get('userId')

        if not user_id:
            return jsonify({"error": "Missing userId parameter"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        today = date.today()

        if (user_id == "7"):
            query = """
            SELECT 
                p.projectId AS id, 
                p.name AS title, 
                p.description, 
                0 AS progress
            FROM Projects p
            WHERE p.endDate >= %s
            """
            cursor.execute(query, (today,))
        else:
            query = """
            SELECT 
                p.projectId AS id, 
                p.name AS title, 
                p.description, 
                CEIL(IFNULL(labeled_count, 0) / IFNULL(total_images, 1) * 100) AS progress
            FROM Projects p
            LEFT JOIN (
                SELECT i.project_id, COUNT(DISTINCT l.ImageID) AS labeled_count
                FROM Labels l
                JOIN Images i ON l.ImageID = i.id
                WHERE l.LabellerID = %s
                GROUP BY i.project_id
            ) labeled ON p.projectId = labeled.project_id
            LEFT JOIN (
                SELECT project_id, COUNT(*) AS total_images
                FROM Images
                GROUP BY project_id
            ) img_count ON p.projectId = img_count.project_id
            WHERE p.endDate >= %s
            """
            cursor.execute(query, (user_id, today))

        
        projects = cursor.fetchall()

        return jsonify({"projects": projects}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@user_project_blueprint.route('/api/client_projects', methods=['GET'])
def get_client_projects():
    conn = None
    cursor = None
    try:
        client_id = request.args.get('clientId')

        if not client_id:
            return jsonify({"error": "Missing userId parameter"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        today = date.today()

        query = """
        SELECT 
            p.projectId AS id, 
            p.name AS title, 
            p.description, 
            CEIL(IFNULL(labeled_count, 0)) AS progress
        FROM Projects p
        LEFT JOIN (
            SELECT i.project_id, COUNT(l.ImageID) AS labeled_count
            FROM Labels l
            JOIN Images i ON l.ImageID = i.id
            GROUP BY i.project_id
        ) labeled ON p.projectId = labeled.project_id
        WHERE p.endDate >= %s AND p.clientId = %s
        """
        cursor.execute(query, (today, client_id))

        
        projects = cursor.fetchall()

        return jsonify({"projects": projects}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@user_project_blueprint.route('/api/getImages', methods=['GET'])
def get_images():
    conn = None
    cursor = None
    try:
        project_id = request.args.get('projectId')
        limit = request.args.get('limit', default=10, type=int)
        offset = request.args.get('offset', default=0, type=int)
        user_id = request.args.get('userId')

        if not project_id or not user_id:
            return jsonify({"error": "Missing projectId or userId parameter"}), 400

        project_id = int(project_id)
        user_id = int(user_id)

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if (user_id == 7):
            query = """
                SELECT i.*
                FROM Images i
                WHERE i.project_id = %s
                LIMIT %s OFFSET %s
                """
            cursor.execute(query, (project_id, limit, offset))
        else:
            query = """
                SELECT i.*
                FROM Images i
                LEFT JOIN Labels l ON i.id = l.ImageID AND l.LabellerID = %s
                WHERE i.project_id = %s AND l.ImageID IS NULL
                ORDER BY i.confidence ASC
                LIMIT %s OFFSET %s
                """
            cursor.execute(query, (user_id, project_id, limit, offset))
        
        
        images = cursor.fetchall()

        for image in images:
            image['image'] = base64.b64encode(image['image']).decode('utf-8')

        return jsonify({"images": images}), 200

    except Exception as e:
        print(str(e))
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@user_project_blueprint.route('/api/project/<int:project_id>', methods=['GET'])
def get_project_categories(project_id):
    conn = None
    cursor = None
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
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@user_project_blueprint.route('/api/update-user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    conn = None
    cursor = None
    try:
        data = request.get_json()
        email = data.get('email')
        user_type = data.get('userType')
        profile_picture_base64 = data.get('profilePicture')

        conn = get_db_connection()
        cursor = conn.cursor()

        profile_picture_blob = None
        if profile_picture_base64:
            profile_picture_blob = base64.b64decode(profile_picture_base64)

        if user_type == 'client':
            name = data.get('name')
            industry = data.get('industry')
            typical_projects = data.get('typicalProj')

            update_query = """
            UPDATE Clients 
            SET email = %s, name = %s, industry = %s, typical_projects = %s 
            """
            values = [email, name, industry, typical_projects]

        elif user_type == 'labeller':
            first_name = data.get('firstName')
            last_name = data.get('lastName')
            skills = data.get('skills')
            availability = data.get('availability')

            update_query = """
            UPDATE Labellers 
            SET email = %s, first_name = %s, last_name = %s, skills = %s, availability = %s
            """
            values = [email, first_name, last_name, skills, availability]

        if profile_picture_blob:
            update_query += ", profile_picture = %s"
            values.append(profile_picture_blob)

        update_query += " WHERE id = %s"
        values.append(user_id)

        cursor.execute(update_query, tuple(values))
        conn.commit()

        return jsonify({'message': 'User updated successfully'}), 200

    except Exception as e:
        print(str(e))
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@user_project_blueprint.route('/api/get_original_image', methods=['GET'])
def get_original_image():
    conn = None
    cursor = None
    try:
        image_id = request.args.get('imageId')

        if not image_id:
            return jsonify({"error": "Missing imageId parameter"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT image FROM my_image_db.OriginalImages WHERE ProjectId = %s
        """
        cursor.execute(query, (image_id,))
        result = cursor.fetchone()
        
        if not result:
            return jsonify({"error": "Image not found"}), 404

        # Properly handle the binary image data
        image_data = io.BytesIO(result['image'])
        return send_file(image_data, mimetype='image/png')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()