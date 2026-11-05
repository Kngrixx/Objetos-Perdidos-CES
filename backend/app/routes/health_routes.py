from flask import Blueprint
from app.controllers.health_controller import (
    health_controller,
    health_status_controller,
    db_status_controller
)

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    return health_controller()


@health_bp.route('/health/status', methods=['GET'])
def health_status():
    return health_status_controller()


@health_bp.route('/health/db_status', methods=['GET'])
def health_db_status():
    return db_status_controller()
