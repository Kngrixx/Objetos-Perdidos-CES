from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.common.constants import ADMIN, OPERADOR
from app.common.security import roles_required
from app.controllers.object_photo_controller import (
    list_photos_controller,
    add_photos_controller,
    photo_file_controller,
    inactivate_photo_controller,
    reactivate_photo_controller
)

object_photo_bp = Blueprint('object_photos', __name__)


# CONSULTA no ve fotos (podrían exponer información personal): 403.
@object_photo_bp.route('/object-lost/<int:object_id>/photos', methods=['GET'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def list_photos_route(object_id):
    return list_photos_controller(object_id)


@object_photo_bp.route('/object-lost/<int:object_id>/photos', methods=['POST'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def add_photos_route(object_id):
    return add_photos_controller(object_id)


@object_photo_bp.route('/object-photos/<int:photo_id>/file', methods=['GET'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def photo_file_route(photo_id):
    return photo_file_controller(photo_id)


@object_photo_bp.route('/object-photos/<int:photo_id>/inactivate', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def inactivate_photo_route(photo_id):
    return inactivate_photo_controller(photo_id)


@object_photo_bp.route('/object-photos/<int:photo_id>/reactivate', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def reactivate_photo_route(photo_id):
    return reactivate_photo_controller(photo_id)
