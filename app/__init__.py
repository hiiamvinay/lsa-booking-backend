from flask import Flask

from app.config import config
from app.extensions import db, migrate
from app.models.parent import Parent
from app.models.lsa import LSAProfile
from app.models.skill import Skill, LSASkill
from app.models.payment import Payment
from app.models.booking import BookingRequest
from app.routes.booking_routes import booking_bp
from app.routes.lsa_routes import lsa_bp
from dotenv import load_dotenv
import os

load_dotenv()

def create_app(config_name=None):
    app = Flask(__name__)

    if config_name is None:
        config_name = os.getenv("FLASK_CONFIG", "development")
    
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    app.register_blueprint(lsa_bp)
    app.register_blueprint(booking_bp)

    return app
