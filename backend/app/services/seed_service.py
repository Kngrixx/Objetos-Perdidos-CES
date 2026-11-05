from flask import current_app
from sqlalchemy import select
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models.role import Role
from app.models.user import User
from app.models.campus import Campus
from app.models.block import Block
from app.models.department import Department
from app.models.object_category import ObjectCategory
from app.models.object_type import ObjectType
from app.common.constants import ADMIN
from app.common.normalization import normalize_name, normalize_email
from app.common.seed_data import ROLES, CAMPUSES, DEPARTMENTS, OBJECT_TYPES

# Seed reproducible: se puede ejecutar varias veces sin crear duplicados
# (antes de insertar busca por nombre normalizado).


def get_or_create_role(name, description, summary):
    role = db.session.execute(select(Role).where(Role.name == name)).scalar_one_or_none()
    if role is None:
        role = Role(name=name, description=description)
        db.session.add(role)
        db.session.flush()
        summary["roles"] += 1
    return role


def get_or_create_campus(name, summary):
    campus = db.session.execute(
        select(Campus).where(Campus.normalized_name == normalize_name(name))
    ).scalar_one_or_none()
    if campus is None:
        campus = Campus(name=name, normalized_name=normalize_name(name))
        db.session.add(campus)
        db.session.flush()
        summary["campuses"] += 1
    return campus


def get_or_create_block(campus, name, summary):
    block = db.session.execute(
        select(Block).where(Block.campus_id == campus.id, Block.normalized_name == normalize_name(name))
    ).scalar_one_or_none()
    if block is None:
        block = Block(campus_id=campus.id, name=name, normalized_name=normalize_name(name))
        db.session.add(block)
        db.session.flush()
        summary["blocks"] += 1
    return block


def get_or_create_department(name, summary):
    department = db.session.execute(
        select(Department).where(Department.normalized_name == normalize_name(name))
    ).scalar_one_or_none()
    if department is None:
        department = Department(name=name, normalized_name=normalize_name(name))
        db.session.add(department)
        db.session.flush()
        summary["departments"] += 1
    return department


def get_or_create_category(name, summary):
    category = db.session.execute(
        select(ObjectCategory).where(ObjectCategory.normalized_name == normalize_name(name))
    ).scalar_one_or_none()
    if category is None:
        category = ObjectCategory(name=name, normalized_name=normalize_name(name))
        db.session.add(category)
        db.session.flush()
        summary["categories"] += 1
    return category


def get_or_create_object_type(category, name, summary):
    object_type = db.session.execute(
        select(ObjectType).where(
            ObjectType.category_id == category.id,
            ObjectType.normalized_name == normalize_name(name)
        )
    ).scalar_one_or_none()
    if object_type is None:
        object_type = ObjectType(category_id=category.id, name=name, normalized_name=normalize_name(name))
        db.session.add(object_type)
        db.session.flush()
        summary["object_types"] += 1
    return object_type


def create_first_admin(summary):
    """El primer administrador se crea solo aquí (seed controlado), nunca por registro público."""
    email = normalize_email(current_app.config["SEED_ADMIN_EMAIL"])
    admin = db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if admin is not None:
        return admin
    admin_role = db.session.execute(select(Role).where(Role.name == ADMIN)).scalar_one()
    admin = User(
        identification=current_app.config["SEED_ADMIN_IDENTIFICATION"],
        full_name=current_app.config["SEED_ADMIN_NAME"],
        email=email,
        password_hash=generate_password_hash(current_app.config["SEED_ADMIN_PASSWORD"]),
        role_id=admin_role.id
    )
    db.session.add(admin)
    db.session.flush()
    summary["admin"] = 1
    return admin


def run_seed():
    summary = {"roles": 0, "campuses": 0, "blocks": 0, "departments": 0,
               "categories": 0, "object_types": 0, "admin": 0}

    for name, description in ROLES:
        get_or_create_role(name, description, summary)

    for campus_name, block_names in CAMPUSES.items():
        campus = get_or_create_campus(campus_name, summary)
        for block_name in block_names:
            get_or_create_block(campus, block_name, summary)

    for department_name in DEPARTMENTS:
        get_or_create_department(department_name, summary)

    for category_name, type_names in OBJECT_TYPES.items():
        category = get_or_create_category(category_name, summary)
        for type_name in type_names:
            get_or_create_object_type(category, type_name, summary)

    create_first_admin(summary)
    db.session.commit()
    return summary
