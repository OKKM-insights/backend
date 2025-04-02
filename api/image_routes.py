# pkgs
from flask import Blueprint, send_file, request, jsonify
import io

# modules
from services.image_service import get_image
from services.core_img_db_connector import get_db_connection

image_blueprint = Blueprint('image_routes', __name__)

@image_blueprint.route('/api/image', methods=['GET'])
def get_image_route():

    image_path = get_image()
    
    return send_file(image_path, mimetype='image/png')

@image_blueprint.route('/api/get_original_image', methods=['GET'])
def get_original_image():
    conn = None
    cursor = None
    try:
        image_id = request.args.get('projectId')

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
