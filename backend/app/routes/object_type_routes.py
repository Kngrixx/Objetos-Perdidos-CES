from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.common.constants import ADMIN, OPERADOR
from app.common.security import roles_required
from app.controllers.object_type_controller import (
    list_object_types_controller,
    get_object_type_controller,
    create_object_type_controller,
    update_object_type_controller,
    inactivate_object_type_controller,
    reactivate_object_type_controller
)

object_type_bp = Blueprint('object_type', __name__)


@object_type_bp.route('/object-types', methods=['GET'])
@jwt_required()
def list_object_types_route():
    return list_object_types_controller()


@object_type_bp.route('/object-types/<int:object_type_id>', methods=['GET'])
@jwt_required()
def get_object_type_route(object_type_id):
    return get_object_type_controller(object_type_id)


@object_type_bp.route('/object-types', methods=['POST'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def create_object_type_route():
    return create_object_type_controller()


@object_type_bp.route('/object-types/<int:object_type_id>', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def update_object_type_route(object_type_id):
    return update_object_type_controller(object_type_id)


@object_type_bp.route('/object-types/<int:object_type_id>/inactivate', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def inactivate_object_type_route(object_type_id):
    return inactivate_object_type_controller(object_type_id)


@object_type_bp.route('/object-types/<int:object_type_id>/reactivate', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def reactivate_object_type_route(object_type_id):
    return reactivate_object_type_controller(object_type_id)
