from sqlalchemy import select, func, or_
from app.extensions import db
from app.models.person import Person
from app.models.department import Department
from app.models.claim import Claim
from app.models.return_record import ReturnRecord
from app.common.constants import PENDIENTE, ACEPTADA
from app.common.errors import AppError
from app.common.normalization import normalize_email
from app.common.pagination import paginate
from app.common.dates import utc_now
from app.services.audit_service import add_audit_log, snapshot, only_changes


def get_persons_by_filter(filters, page, page_size):
    query = select(Person)
    if filters.get("id") is not None:
        query = query.where(Person.id == filters["id"])
    if filters.get("identification"):
        query = query.where(Person.identification.ilike(f'%{filters["identification"]}%'))
    if filters.get("name"):
        query = query.where(Person.full_name.ilike(f'%{filters["name"]}%'))
    if filters.get("text"):
        pattern = f'%{filters["text"]}%'
        query = query.where(or_(Person.full_name.ilike(pattern), Person.identification.ilike(pattern)))
    if filters.get("affiliation_type"):
        query = query.where(Person.affiliation_type == filters["affiliation_type"])
    if filters.get("department_id") is not None:
        query = query.where(Person.department_id == filters["department_id"])
    if filters.get("is_active") is not None:
        query = query.where(Person.is_active == filters["is_active"])
    query = query.order_by(Person.full_name, Person.id)
    return paginate(query, page, page_size)


def get_person_by_id(person_id, lock=False):
    query = select(Person).where(Person.id == person_id)
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    person = db.session.execute(query).scalar_one_or_none()
    if person is None:
        raise AppError("Persona no encontrada.", 404)
    return person


def check_active_department(department_id):
    if department_id is None:
        return
    department = db.session.get(Department, department_id)
    if department is None:
        raise AppError("La dependencia indicada no existe.", 400)
    if not department.is_active:
        raise AppError("La dependencia indicada está inactiva.", 400)


def check_duplicate_identification(identification, current_id=None):
    query = select(Person).where(Person.identification == identification)
    if current_id is not None:
        query = query.where(Person.id != current_id)
    existing = db.session.execute(query).scalar_one_or_none()
    if existing:
        raise AppError("Ya existe una persona con esa identificación.", 409, {"existing_id": existing.id})


def create_person(data, actor):
    check_duplicate_identification(data["identification"])
    check_active_department(data.get("department_id"))
    person = Person(
        identification=data["identification"],
        full_name=data["full_name"],
        affiliation_type=data["affiliation_type"],
        department_id=data.get("department_id"),
        email=normalize_email(data["email"]) if data.get("email") else None,
        phone=data.get("phone"),
        created_by=actor.id,
        updated_by=actor.id
    )
    db.session.add(person)
    db.session.flush()
    add_audit_log("person", person.id, "CREATE", actor.id, after=snapshot(person))
    db.session.commit()
    return person


def update_person(person_id, data, reason, actor):
    person = get_person_by_id(person_id)
    if not person.is_active:
        raise AppError("No se puede editar una persona inactiva.", 409)
    before = snapshot(person)

    if "identification" in data:
        check_duplicate_identification(data["identification"], person.id)
        person.identification = data["identification"]
    if "full_name" in data:
        person.full_name = data["full_name"]
    if "affiliation_type" in data:
        person.affiliation_type = data["affiliation_type"]
    if "department_id" in data:
        if data["department_id"] != person.department_id:
            check_active_department(data["department_id"])
        person.department_id = data["department_id"]
    if "email" in data:
        person.email = normalize_email(data["email"]) if data["email"] else None
    if "phone" in data:
        person.phone = data["phone"]

    person.updated_by = actor.id
    db.session.flush()
    changes_before, changes_after = only_changes(before, snapshot(person))
    add_audit_log("person", person.id, "UPDATE", actor.id, reason, changes_before, changes_after)
    db.session.commit()
    return person


def count_pending_operations(person_id):
    """Reclamaciones PENDIENTES o ACEPTADAS que aún no tienen devolución."""
    return db.session.execute(
        select(func.count(Claim.id))
        .outerjoin(ReturnRecord, ReturnRecord.claim_id == Claim.id)
        .where(
            Claim.claimant_person_id == person_id,
            Claim.is_active.is_(True),
            Claim.status.in_([PENDIENTE, ACEPTADA]),
            ReturnRecord.id.is_(None)
        )
    ).scalar_one()


def inactivate_person(person_id, reason, actor):
    person = get_person_by_id(person_id, lock=True)
    if not person.is_active:
        raise AppError("La persona ya está inactiva.", 409)
    pending = count_pending_operations(person.id)
    if pending > 0:
        raise AppError(
            f"No se puede inactivar la persona: tiene {pending} reclamación(es) pendiente(s) "
            f"o aceptada(s) sin devolución.", 409
        )
    before = snapshot(person)
    person.is_active = False
    person.inactivated_at = utc_now()
    person.inactivated_by = actor.id
    person.inactivation_reason = reason
    person.updated_by = actor.id
    db.session.flush()
    add_audit_log("person", person.id, "INACTIVATE", actor.id, reason, before, snapshot(person))
    db.session.commit()
    return person


def reactivate_person(person_id, reason, actor):
    person = get_person_by_id(person_id, lock=True)
    if person.is_active:
        raise AppError("La persona ya está activa.", 409)
    before = snapshot(person)
    person.is_active = True
    person.inactivated_at = None
    person.inactivated_by = None
    person.inactivation_reason = None
    person.updated_by = actor.id
    db.session.flush()
    add_audit_log("person", person.id, "REACTIVATE", actor.id, reason, before, snapshot(person))
    db.session.commit()
    return person
