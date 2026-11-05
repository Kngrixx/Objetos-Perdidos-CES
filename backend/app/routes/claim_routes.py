from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.common.constants import ADMIN, OPERADOR
from app.common.security import roles_required
from app.controllers.claim_controller import (
    list_claims_controller,
    get_claim_controller,
    create_claim_controller,
    update_claim_controller,
    decide_claim_controller,
    inactivate_claim_controller,
    reactivate_claim_controller
)

claim_bp = Blueprint('claims', __name__)


@claim_bp.route('/claims', methods=['POST'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def create_claim_route():
    return create_claim_controller()


@claim_bp.route('/claims', methods=['GET'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def list_claims_route():
    return list_claims_controller()


@claim_bp.route('/claims/<int:claim_id>', methods=['GET'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def get_claim_route(claim_id):
    return get_claim_controller(claim_id)


@claim_bp.route('/claims/<int:claim_id>', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def update_claim_route(claim_id):
    return update_claim_controller(claim_id)


@claim_bp.route('/claims/<int:claim_id>/decision', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def decide_claim_route(claim_id):
    return decide_claim_controller(claim_id)


@claim_bp.route('/claims/<int:claim_id>/inactivate', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def inactivate_claim_route(claim_id):
    return inactivate_claim_controller(claim_id)


@claim_bp.route('/claims/<int:claim_id>/reactivate', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def reactivate_claim_route(claim_id):
    return reactivate_claim_controller(claim_id)
