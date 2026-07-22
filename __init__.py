import os
from flask import Flask
from .extensions import db
from .config import config
from .model import Utilisateur
from .routes import routes
from flask_login import LoginManager


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "default")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Init DB
    db.init_app(app)

    # Blueprints
    app.register_blueprint(routes, url_prefix="/")

    # Create tables
    with app.app_context():
        #db.drop_all()
        db.create_all()

    # Login manager
    login_manager = LoginManager()
    login_manager.login_message = "S'il vous plaît connectez-vous à notre plateforme."
    
    # ⚠️ adapte selon ton blueprint
    login_manager.login_view = "routes.login"

    login_manager.init_app(app)

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Utilisateur, int(user_id))

    return app
