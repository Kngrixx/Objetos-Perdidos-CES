from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.common.constants import ADMIN
from app.common.security import roles_required
from app.controllers.department_controller import (
    list_departments_controller,
    get_department_controller,
    create_department_controller,
    update_department_controller,
    inactivate_department_controller,
    reactivate_department_controller
)

department_bp = Blueprint('department', __name__)


@department_bp.route('/departments', methods=['GET'])
@jwt_required()
def list_departments_route():
    return list_departments_controller()


@department_bp.route('/departments/<int:department_id>', methods=['GET'])
@jwt_required()
def get_department_route(department_id):
    return get_department_controller(department_id)


@department_bp.route('/departments', methods=['POST'])
@jwt_required()
@roles_required(ADMIN)
def create_department_route():
    return create_department_controller()


@department_bp.route('/departments/<int:department_id>', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def update_department_route(department_id):
    return update_department_controller(department_id)


@department_bp.route('/departments/<int:department_id>/inactivate', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def inactivate_department_route(department_id):
    return inactivate_department_controller(department_id)


@department_bp.route('/departments/<int:department_id>/reactivate', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def reactivate_department_route(department_id):
    return reactivate_department_controller(department_id)
