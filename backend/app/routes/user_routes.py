from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.common.constants import ADMIN
from app.common.security import roles_required
from app.controllers.user_controller import (
    list_users_controller,
    get_user_controller,
    update_user_controller,
    inactivate_user_controller,
    reactivate_user_controller
)

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
@jwt_required()
@roles_required(ADMIN)
def list_users_route():
    return list_users_controller()


@user_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
@roles_required(ADMIN)
def get_user_route(user_id):
    return get_user_controller(user_id)


@user_bp.route('/users/<int:user_id>', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def update_user_route(user_id):
    return update_user_controller(user_id)


@user_bp.route('/users/<int:user_id>/inactivate', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def inactivate_user_route(user_id):
    return inactivate_user_controller(user_id)


@user_bp.route('/users/<int:user_id>/reactivate', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def reactivate_user_route(user_id):
    return reactivate_user_controller(user_id)
