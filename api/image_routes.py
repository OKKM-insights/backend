# pkgs
from flask import Blueprint, send_file

# modules
from services.image_service import get_image

image_blueprint = Blueprint('image_routes', __name__)

@image_blueprint.route('/api/image', methods=['GET'])
def get_image_route():

    image_path = get_image()
    
    return send_file(image_path, mimetype='image/png')

