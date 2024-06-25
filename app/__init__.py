from flask import Flask
from config import Config
from .extensions import db, migrate, login, session

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    # Configure Flask-Session to use the existing SQLAlchemy instance
    app.config['SESSION_SQLALCHEMY'] = db
    session.init_app(app)

    from .routes import init_routes
    init_routes(app)

    return app
