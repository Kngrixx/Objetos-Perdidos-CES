import os
from flask import Flask
from flask_cors import CORS
from config import Config
from app.extensions import db, migrate, jwt
from app.common.errors import register_error_handlers
from app.common.security import register_jwt_callbacks
from app.routes.health_routes import health_bp
from app.routes.auth_routes import auth_bp
from app.routes.user_routes import user_bp
from app.routes.role_routes import role_bp
from app.routes.campus_routes import campus_bp
from app.routes.block_routes import block_bp
from app.routes.department_routes import department_bp
from app.routes.object_category_routes import object_category_bp
from app.routes.object_type_routes import object_type_bp
from app.routes.person_routes import person_bp
from app.routes.object_lost_routes import object_lost_bp
from app.routes.object_photo_routes import object_photo_bp
from app.routes.claim_routes import claim_bp
from app.routes.return_routes import return_bp
from app.routes.inventory_routes import inventory_bp
from app.routes.audit_routes import audit_bp
from app.routes.dashboard_routes import dashboard_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if not app.config.get("SQLALCHEMY_DATABASE_URI"):
        raise RuntimeError("Falta DATABASE_URL en el archivo .env (copie .env.example a .env).")
    if not app.config.get("JWT_SECRET_KEY") or len(app.config["JWT_SECRET_KEY"]) < 32:
        raise RuntimeError("JWT_SECRET_KEY no está en el .env o tiene menos de 32 caracteres.")

    app.json.ensure_ascii = False  # tildes legibles en el JSON
    app.json.sort_keys = False     # respeta el orden ok, message, data
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": app.config["CORS_ALLOWED_ORIGINS"]
            }
        },
        supports_credentials=True,
        expose_headers=["Content-Disposition", "X-Total-Count"],
    )
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    register_jwt_callbacks(jwt)
    register_error_handlers(app)

    from app import models

    app.register_blueprint(
        health_bp,
        url_prefix='/api'
    )
    app.register_blueprint(
        auth_bp,
        url_prefix='/api'
    )
    app.register_blueprint(
        user_bp,
        url_prefix='/api'
    )
    app.register_blueprint(
        role_bp,
        url_prefix='/api'
    )
    app.register_blueprint(
        campus_bp,
        url_prefix='/api'
    )
    app.register_blueprint(
        block_bp,
        url_prefix='/api'
    )
    app.register_blueprint(
        department_bp,
        url_prefix='/api'
    )
    app.register_blueprint(
        object_category_bp,
        url_prefix='/api'
    )
    app.register_blueprint(
        object_type_bp,
        url_prefix='/api'
    )
    app.register_blueprint(
        person_bp,
        url_prefix='/api'
    )
    app.register_blueprint(
        object_lost_bp,
        url_prefix='/api'
    )
    app.register_blueprint(
        object_photo_bp,
        url_prefix='/api'
    )
    app.register_blueprint(
        claim_bp,
        url_prefix='/api'
    )
    app.register_blueprint(
        return_bp,
        url_prefix='/api'
    )
    app.register_blueprint(
        inventory_bp,
        url_prefix='/api'
    )
    app.register_blueprint(
        audit_bp,
        url_prefix='/api'
    )
    app.register_blueprint(
        dashboard_bp,
        url_prefix='/api'
    )

    return app
