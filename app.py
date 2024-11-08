# pkgs
from flask import Flask

# modules
from api.image_routes import image_blueprint


def create_app():
    app = Flask(__name__)
    app.register_blueprint(image_blueprint)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
