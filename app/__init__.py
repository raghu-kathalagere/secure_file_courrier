import os
from flask import Flask
from .extensions import db, login_manager, bcrypt

def create_app(config_class="config.Config"):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    # Create upload folder if not exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Register blueprints
    from .auth.routes import auth_bp
    from .files.routes import files_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(files_bp)

    # Create tables
    with app.app_context():
        db.create_all()

    return app
