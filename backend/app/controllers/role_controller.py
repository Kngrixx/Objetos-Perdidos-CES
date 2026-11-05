from app.common.responses import success_response
from app.services.role_service import get_all_roles


def role_to_dict(role):
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
    }


def list_roles_controller():
    roles = get_all_roles()
    return success_response("Consulta exitosa.", [role_to_dict(role) for role in roles])
