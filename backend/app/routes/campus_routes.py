from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.common.constants import ADMIN
from app.common.security import roles_required
from app.controllers.campus_controller import (
    list_campuses_controller,
    get_campus_controller,
    create_campus_controller,
    update_campus_controller,
    inactivate_campus_controller,
    reactivate_campus_controller
)

campus_bp = Blueprint('campus', __name__)


@campus_bp.route('/campuses', methods=['GET'])
@jwt_required()
def list_campuses_route():
    return list_campuses_controller()


@campus_bp.route('/campuses/<int:campus_id>', methods=['GET'])
@jwt_required()
def get_campus_route(campus_id):
    return get_campus_controller(campus_id)


@campus_bp.route('/campuses', methods=['POST'])
@jwt_required()
@roles_required(ADMIN)
def create_campus_route():
    return create_campus_controller()


@campus_bp.route('/campuses/<int:campus_id>', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def update_campus_route(campus_id):
    return update_campus_controller(campus_id)


@campus_bp.route('/campuses/<int:campus_id>/inactivate', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def inactivate_campus_route(campus_id):
    return inactivate_campus_controller(campus_id)


@campus_bp.route('/campuses/<int:campus_id>/reactivate', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def reactivate_campus_route(campus_id):
    return reactivate_campus_controller(campus_id)
