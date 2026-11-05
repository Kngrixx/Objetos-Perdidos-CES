from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.common.constants import ADMIN, OPERADOR
from app.common.security import roles_required
from app.controllers.object_lost_controller import (
    list_objects_controller,
    get_object_controller,
    create_object_controller,
    update_object_controller,
    inactivate_object_controller,
    reactivate_object_controller,
    administrative_correction_controller
)

object_lost_bp = Blueprint('object_lost', __name__)


@object_lost_bp.route('/object-lost', methods=['POST'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def create_object_route():
    return create_object_controller()


# GET: todos los roles; el controller aplica la proyección reducida para CONSULTA.
@object_lost_bp.route('/object-lost', methods=['GET'])
@jwt_required()
def list_objects_route():
    return list_objects_controller()


@object_lost_bp.route('/object-lost/<int:object_id>', methods=['GET'])
@jwt_required()
def get_object_route(object_id):
    return get_object_controller(object_id)


@object_lost_bp.route('/object-lost/<int:object_id>', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def update_object_route(object_id):
    return update_object_controller(object_id)


@object_lost_bp.route('/object-lost/<int:object_id>/inactivate', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def inactivate_object_route(object_id):
    return inactivate_object_controller(object_id)


@object_lost_bp.route('/object-lost/<int:object_id>/reactivate', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def reactivate_object_route(object_id):
    return reactivate_object_controller(object_id)


@object_lost_bp.route('/object-lost/<int:object_id>/administrative-correction', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def administrative_correction_route(object_id):
    return administrative_correction_controller(object_id)
