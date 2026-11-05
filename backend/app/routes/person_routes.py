from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.common.constants import ADMIN, OPERADOR
from app.common.security import roles_required
from app.controllers.person_controller import (
    list_persons_controller,
    get_person_controller,
    create_person_controller,
    update_person_controller,
    inactivate_person_controller,
    reactivate_person_controller
)

person_bp = Blueprint('persons', __name__)


@person_bp.route('/persons', methods=['GET'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def list_persons_route():
    return list_persons_controller()


@person_bp.route('/persons/<int:person_id>', methods=['GET'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def get_person_route(person_id):
    return get_person_controller(person_id)


@person_bp.route('/persons', methods=['POST'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def create_person_route():
    return create_person_controller()


@person_bp.route('/persons/<int:person_id>', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def update_person_route(person_id):
    return update_person_controller(person_id)


@person_bp.route('/persons/<int:person_id>/inactivate', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def inactivate_person_route(person_id):
    return inactivate_person_controller(person_id)


@person_bp.route('/persons/<int:person_id>/reactivate', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def reactivate_person_route(person_id):
    return reactivate_person_controller(person_id)
