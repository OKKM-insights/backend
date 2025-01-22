# pkgs
from flask import Flask
from waitress import serve
from flask_cors import CORS

# modules
from api.image_routes import image_blueprint


def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "https://orbitwatch.xyz"}})
    app.register_blueprint(image_blueprint)
    return app

app = create_app()

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5050)


