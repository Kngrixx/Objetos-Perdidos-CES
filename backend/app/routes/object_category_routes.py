from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.common.constants import ADMIN
from app.common.security import roles_required
from app.controllers.object_category_controller import (
    list_categories_controller,
    get_category_controller,
    create_category_controller,
    update_category_controller,
    inactivate_category_controller,
    reactivate_category_controller
)

object_category_bp = Blueprint('object_category', __name__)


@object_category_bp.route('/object-categories', methods=['GET'])
@jwt_required()
def list_categories_route():
    return list_categories_controller()


@object_category_bp.route('/object-categories/<int:category_id>', methods=['GET'])
@jwt_required()
def get_category_route(category_id):
    return get_category_controller(category_id)


@object_category_bp.route('/object-categories', methods=['POST'])
@jwt_required()
@roles_required(ADMIN)
def create_category_route():
    return create_category_controller()


@object_category_bp.route('/object-categories/<int:category_id>', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def update_category_route(category_id):
    return update_category_controller(category_id)


@object_category_bp.route('/object-categories/<int:category_id>/inactivate', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def inactivate_category_route(category_id):
    return inactivate_category_controller(category_id)


@object_category_bp.route('/object-categories/<int:category_id>/reactivate', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def reactivate_category_route(category_id):
    return reactivate_category_controller(category_id)
