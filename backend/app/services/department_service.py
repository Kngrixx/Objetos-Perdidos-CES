from sqlalchemy import select, func
from app.extensions import db
from app.models.department import Department
from app.models.object_lost import ObjectLost
from app.common.constants import DISPONIBLE
from app.common.errors import AppError
from app.common.normalization import normalize_name
from app.common.pagination import paginate
from app.common.dates import utc_now
from app.services.audit_service import add_audit_log, snapshot, only_changes


def get_departments_by_filter(filters, page, page_size):
    query = select(Department)
    if filters.get("id") is not None:
        query = query.where(Department.id == filters["id"])
    if filters.get("name"):
        query = query.where(Department.normalized_name.contains(normalize_name(filters["name"]), autoescape=True))
    if filters.get("is_active") is not None:
        query = query.where(Department.is_active == filters["is_active"])
    query = query.order_by(Department.name, Department.id)
    return paginate(query, page, page_size)


def get_department_by_id(department_id, lock=False):
    query = select(Department).where(Department.id == department_id)
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    department = db.session.execute(query).scalar_one_or_none()
    if department is None:
        raise AppError("Dependencia no encontrada.", 404)
    return department


def check_duplicate_name(normalized, current_id=None):
    query = select(Department).where(Department.normalized_name == normalized)
    if current_id is not None:
        query = query.where(Department.id != current_id)
    existing = db.session.execute(query).scalar_one_or_none()
    if existing:
        raise AppError(f'Ya existe una dependencia con ese nombre: "{existing.name}".', 409)


def create_department(name, actor):
    normalized = normalize_name(name)
    check_duplicate_name(normalized)
    department = Department(name=name, normalized_name=normalized, created_by=actor.id, updated_by=actor.id)
    db.session.add(department)
    db.session.flush()
    add_audit_log("department", department.id, "CREATE", actor.id, after=snapshot(department))
    db.session.commit()
    return department


def update_department(department_id, name, reason, actor):
    department = get_department_by_id(department_id)
    if not department.is_active:
        raise AppError("No se puede editar una dependencia inactiva.", 409)
    before = snapshot(department)
    normalized = normalize_name(name)
    check_duplicate_name(normalized, department.id)
    department.name = name
    department.normalized_name = normalized
    department.updated_by = actor.id
    db.session.flush()
    changes_before, changes_after = only_changes(before, snapshot(department))
    add_audit_log("department", department.id, "UPDATE", actor.id, reason, changes_before, changes_after)
    db.session.commit()
    return department


def inactivate_department(department_id, reason, actor):
    department = get_department_by_id(department_id, lock=True)
    if not department.is_active:
        raise AppError("La dependencia ya está inactiva.", 409)
    available_objects = db.session.execute(
        select(func.count(ObjectLost.id)).where(
            ObjectLost.finder_department_id == department.id,
            ObjectLost.is_active.is_(True),
            ObjectLost.status == DISPONIBLE
        )
    ).scalar_one()
    if available_objects > 0:
        raise AppError(
            f"No se puede inactivar la dependencia: {available_objects} objeto(s) activo(s) "
            f"DISPONIBLE(S) dependen de ella.", 409
        )
    before = snapshot(department)
    department.is_active = False
    department.inactivated_at = utc_now()
    department.inactivated_by = actor.id
    department.inactivation_reason = reason
    department.updated_by = actor.id
    db.session.flush()
    add_audit_log("department", department.id, "INACTIVATE", actor.id, reason, before, snapshot(department))
    db.session.commit()
    return department


def reactivate_department(department_id, reason, actor):
    department = get_department_by_id(department_id, lock=True)
    if department.is_active:
        raise AppError("La dependencia ya está activa.", 409)
    before = snapshot(department)
    department.is_active = True
    department.inactivated_at = None
    department.inactivated_by = None
    department.inactivation_reason = None
    department.updated_by = actor.id
    db.session.flush()
    add_audit_log("department", department.id, "REACTIVATE", actor.id, reason, before, snapshot(department))
    db.session.commit()
    return department
