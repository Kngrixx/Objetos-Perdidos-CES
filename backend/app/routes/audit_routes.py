from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.common.constants import ADMIN, OPERADOR
from app.common.security import roles_required
from app.controllers.audit_controller import (
    list_audit_logs_controller,
    object_history_controller
)

audit_bp = Blueprint('audit', __name__)


@audit_bp.route('/audit-logs', methods=['GET'])
@jwt_required()
@roles_required(ADMIN)
def list_audit_logs_route():
    return list_audit_logs_controller()


@audit_bp.route('/object-lost/<int:object_id>/history', methods=['GET'])
@jwt_required()
@roles_required(ADMIN, OPERADOR)
def object_history_route(object_id):
    return object_history_controller(object_id)
