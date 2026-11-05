from app.common.constants import AFFILIATION_TYPES
from app.common.dates import to_iso
from app.common.pagination import get_page_params
from app.common.responses import success_response, page_data, list_message
from app.common.security import get_current_user
from app.common.validators import (
    get_json_data, require_fields, check_allowed_fields, clean_string, get_reason, to_int,
    validate_email, choice, arg_int, arg_bool, arg_text, arg_choice
)
from app.services.person_service import (
    get_persons_by_filter,
    get_person_by_id,
    create_person,
    update_person,
    inactivate_person,
    reactivate_person
)

PERSON_FIELDS = ["identification", "full_name", "affiliation_type", "department_id", "email", "phone"]


def person_to_dict(person):
    return {
        "id": person.id,
        "identification": person.identification,
        "full_name": person.full_name,
        "affiliation_type": person.affiliation_type,
        "department_id": person.department_id,
        "department_name": person.department.name if person.department else None,
        "email": person.email,
        "phone": person.phone,
        "is_active": person.is_active,
        "created_at": to_iso(person.created_at),
        "updated_at": to_iso(person.updated_at),
        "inactivated_at": to_iso(person.inactivated_at),
        "inactivation_reason": person.inactivation_reason,
    }


def read_person_fields(data):
    """Convierte y valida los campos recibidos (solo los que vienen en la petición)."""
    values = {}
    if "identification" in data:
        values["identification"] = clean_string(data.get("identification"), "identification", 30)
    if "full_name" in data:
        values["full_name"] = clean_string(data.get("full_name"), "full_name", 150)
    if "affiliation_type" in data:
        values["affiliation_type"] = choice(data.get("affiliation_type"), "affiliation_type", AFFILIATION_TYPES)
    if "department_id" in data:
        values["department_id"] = to_int(data.get("department_id"), "department_id")
    if "email" in data:
        email = clean_string(data.get("email"), "email", 200, required=False)
        values["email"] = validate_email(email.lower()) if email else None
    if "phone" in data:
        values["phone"] = clean_string(data.get("phone"), "phone", 30, required=False)
    return values


def list_persons_controller():
    page, page_size = get_page_params()
    filters = {
        "id": arg_int("id"),
        "identification": arg_text("identification"),
        "name": arg_text("name"),
        "text": arg_text("text"),
        "affiliation_type": arg_choice("affiliation_type", AFFILIATION_TYPES),
        "department_id": arg_int("department_id"),
        "is_active": arg_bool("is_active"),
    }
    persons, total = get_persons_by_filter(filters, page, page_size)
    items = [person_to_dict(person) for person in persons]
    return success_response(list_message(total), page_data(items, page, page_size, total))


def get_person_controller(person_id):
    return success_response("Consulta exitosa.", person_to_dict(get_person_by_id(person_id)))


def create_person_controller():
    data = get_json_data()
    check_allowed_fields(data, PERSON_FIELDS)
    require_fields(data, ["identification", "full_name", "affiliation_type"])
    person = create_person(read_person_fields(data), get_current_user())
    return success_response("Persona registrada correctamente.", person_to_dict(person), 201)


def update_person_controller(person_id):
    data = get_json_data()
    check_allowed_fields(data, PERSON_FIELDS + ["reason"])
    person = update_person(person_id, read_person_fields(data), get_reason(data, required=False), get_current_user())
    return success_response("Persona actualizada correctamente.", person_to_dict(person))


def inactivate_person_controller(person_id):
    reason = get_reason(get_json_data())
    person = inactivate_person(person_id, reason, get_current_user())
    return success_response("Persona inactivada correctamente.", person_to_dict(person))


def reactivate_person_controller(person_id):
    reason = get_reason(get_json_data())
    person = reactivate_person(person_id, reason, get_current_user())
    return success_response("Persona reactivada correctamente.", person_to_dict(person))
