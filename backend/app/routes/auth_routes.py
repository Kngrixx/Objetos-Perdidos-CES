from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.controllers.auth_controller import (
    register_controller,
    login_controller,
    me_controller,
    logout_controller,
    forgot_password_controller,
    reset_password_controller,
    change_password_controller
)

auth_bp = Blueprint('auth', __name__)


# ---------- Login (públicas: register y login)
@auth_bp.route('/auth/register', methods=['POST'])
def register_route():
    return register_controller()


@auth_bp.route('/auth/login', methods=['POST'])
def login_route():
    return login_controller()


@auth_bp.route('/auth/me', methods=['GET'])
@jwt_required()
def me_route():
    return me_controller()


@auth_bp.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout_route():
    return logout_controller()


# ---------- Password
@auth_bp.route('/auth/forgot-password', methods=['POST'])
def forgot_password_route():
    return forgot_password_controller()


@auth_bp.route('/auth/reset-password', methods=['POST'])
def reset_password_route():
    return reset_password_controller()


@auth_bp.route('/auth/change-password', methods=['PATCH'])
@jwt_required()
def change_password_route():
    return change_password_controller()
