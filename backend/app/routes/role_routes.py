from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.common.constants import ADMIN
from app.common.security import roles_required
from app.controllers.role_controller import list_roles_controller

role_bp = Blueprint('roles', __name__)


@role_bp.route('/roles', methods=['GET'])
@jwt_required()
@roles_required(ADMIN)
def list_roles_route():
    return list_roles_controller()
