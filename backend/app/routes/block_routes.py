from flask import Blueprint
from flask_jwt_extended import jwt_required
from app.common.constants import ADMIN
from app.common.security import roles_required
from app.controllers.block_controller import (
    list_blocks_controller,
    get_block_controller,
    create_block_controller,
    update_block_controller,
    inactivate_block_controller,
    reactivate_block_controller
)

block_bp = Blueprint('block', __name__)


@block_bp.route('/blocks', methods=['GET'])
@jwt_required()
def list_blocks_route():
    return list_blocks_controller()


@block_bp.route('/blocks/<int:block_id>', methods=['GET'])
@jwt_required()
def get_block_route(block_id):
    return get_block_controller(block_id)


@block_bp.route('/blocks', methods=['POST'])
@jwt_required()
@roles_required(ADMIN)
def create_block_route():
    return create_block_controller()


@block_bp.route('/blocks/<int:block_id>', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def update_block_route(block_id):
    return update_block_controller(block_id)


@block_bp.route('/blocks/<int:block_id>/inactivate', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def inactivate_block_route(block_id):
    return inactivate_block_controller(block_id)


@block_bp.route('/blocks/<int:block_id>/reactivate', methods=['PATCH'])
@jwt_required()
@roles_required(ADMIN)
def reactivate_block_route(block_id):
    return reactivate_block_controller(block_id)
