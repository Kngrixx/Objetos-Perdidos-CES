from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.common.constants import ADMIN
from app.common.security import roles_required
from app.controllers.dashboard_controller import (
    dashboard_summary_controller,
    dashboard_by_category_controller,
    dashboard_by_campus_controller,
    dashboard_recent_controller
)

dashboard_bp = Blueprint('dashboard', __name__)

# Dashboard exclusivo del administrador (enunciado, sección 8).


@dashboard_bp.route('/dashboard/summary', methods=['GET'])
@jwt_required()
@roles_required(ADMIN)
def dashboard_summary_route():
    return dashboard_summary_controller()


@dashboard_bp.route('/dashboard/by-category', methods=['GET'])
@jwt_required()
@roles_required(ADMIN)
def dashboard_by_category_route():
    return dashboard_by_category_controller()


@dashboard_bp.route('/dashboard/by-campus', methods=['GET'])
@jwt_required()
@roles_required(ADMIN)
def dashboard_by_campus_route():
    return dashboard_by_campus_controller()


@dashboard_bp.route('/dashboard/recent', methods=['GET'])
@jwt_required()
@roles_required(ADMIN)
def dashboard_recent_route():
    return dashboard_recent_controller()
