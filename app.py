# pkgs
from flask import Flask
from waitress import serve
from flask_cors import CORS

# modules
from api.image_routes import image_blueprint
from api.account_routes import user_project_blueprint


def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": [
        "https://orbitwatch.xyz", 
        "http://localhost:3000",
        r"^https://deploy-preview-\d+--okkm\.netlify\.app$"
        ]}})
    app.register_blueprint(image_blueprint)
    app.register_blueprint(user_project_blueprint)
    print("launched")
    return app

app = create_app()

if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5050)


