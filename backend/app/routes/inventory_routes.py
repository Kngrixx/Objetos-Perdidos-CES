from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.common.constants import ADMIN, OPERADOR
from app.common.security import roles_required
from app.controllers.inventory_controller import (
    list_inventory_controller,
    inventory_summary_controller,
    export_inventory_controller
)

inventory_bp = Blueprint('inventory', __name__)


@inventory_bp.route('/inventory', methods=['GET'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def list_inventory_route():
    return list_inventory_controller()


@inventory_bp.route('/inventory/summary', methods=['GET'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def inventory_summary_route():
    return inventory_summary_controller()


@inventory_bp.route('/inventory/export', methods=['GET'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def export_inventory_route():
    return export_inventory_controller()
