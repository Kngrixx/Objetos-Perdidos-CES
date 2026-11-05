from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.common.constants import ADMIN, OPERADOR
from app.common.security import roles_required
from app.controllers.return_controller import (
    list_returns_controller,
    get_return_controller,
    create_return_controller,
    receipt_controller
)

return_bp = Blueprint('returns', __name__)


@return_bp.route('/returns', methods=['POST'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def create_return_route():
    return create_return_controller()


@return_bp.route('/returns', methods=['GET'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def list_returns_route():
    return list_returns_controller()


@return_bp.route('/returns/<int:return_id>', methods=['GET'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def get_return_route(return_id):
    return get_return_controller(return_id)


@return_bp.route('/returns/<int:return_id>/receipt', methods=['GET'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def receipt_route(return_id):
    return receipt_controller(return_id)
