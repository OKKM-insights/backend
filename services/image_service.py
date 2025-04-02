import os

def get_image():
    # Assuming the image is stored in the static folder
    # image_path = os.path.join(os.path.dirname(__file__), '../imageDB/airport.png')
    image_path = os.path.join(os.path.dirname(__file__), '../imageDB/labelsdone.png')
    return image_path