from flask import Flask
from flask_cors import CORS
from flask_session import Session
from config import Config
from db_setup import db
from routes.users_routes import users_bp, init_oauth
from routes.events_routes import events_bp
from routes.images_routes import images_bp
from routes.news_routes import news_bp
from routes.videos_routes import videos_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY

    # Sesión
    Session(app)

    # CORS
    CORS(app, supports_credentials=True, resources={r"/api/*": {"origins": Config.CORS_ORIGINS}})

    # DB y OAuth
    db.init_app(app)
    init_oauth(app)

    # Blueprints
    app.register_blueprint(users_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(images_bp)
    app.register_blueprint(news_bp)
    app.register_blueprint(videos_bp)

    # Ruta base
    @app.route("/")
    def index():
        return {"message": "API del sistema deportivo activa"}

    return app

# Variable global para Gunicorn
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

