import io
from datetime import timedelta
from PIL import Image, ImageDraw
from sqlalchemy import select
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models.role import Role
from app.models.user import User
from app.models.campus import Campus
from app.models.block import Block
from app.models.department import Department
from app.models.object_type import ObjectType
from app.models.person import Person
from app.models.object_lost import ObjectLost
from app.models.object_photo import ObjectPhoto
from app.models.claim import Claim
from app.models.return_record import ReturnRecord
from app.common.constants import (
    ADMIN, OPERADOR, CONSULTA, DISPONIBLE, DEVUELTO, ACEPTADA, RECHAZADA, PENDIENTE, RECEIPT_METHOD
)
from app.common.dates import utc_now
from app.common.files import save_photo
from app.common.normalization import normalize_name
from app.services.audit_service import add_audit_log, snapshot
from app.services.object_lost_service import next_object_code

# Dataset FICTICIO para la demostración (enunciado §10): 24 objetos, ambas sedes,
# 5 devueltos, 2 inactivos, fotos y responsables. Nombres e identificaciones inventados.

DEMO_PERSONS = [
    ("DEMO-1001", "Laura Restrepo Demo", "ESTUDIANTE", "Facultad de Medicina"),
    ("DEMO-1002", "Santiago Gómez Demo", "ESTUDIANTE", "Facultad de Ingeniería"),
    ("DEMO-1003", "Valentina Ríos Demo", "EMPLEADO", "Biblioteca"),
    ("DEMO-1004", "Andrés Cano Demo", "CONTRATISTA", "Servicios Generales"),
    ("DEMO-1005", "Camila Zapata Demo", "ESTUDIANTE", "Facultad de Psicología"),
    ("DEMO-1006", "Mateo Arango Demo", "EMPLEADO", "Seguridad y Vigilancia"),
    ("DEMO-1007", "Sofía Herrera Demo", "VISITANTE", None),
    ("DEMO-1008", "Juan Pablo Mejía Demo", "ESTUDIANTE", "Facultad de Odontología"),
    ("DEMO-1009", "Isabela Ortiz Demo", "PROVEEDOR", None),
    ("DEMO-1010", "Tomás Vélez Demo", "ESTUDIANTE", "Facultad de Derecho"),
    ("DEMO-1011", "Mariana López Demo", "EMPLEADO", "Bienestar Universitario"),
    ("DEMO-1012", "Samuel Duque Demo", "ESTUDIANTE", "Facultad de Fisioterapia"),
]

# (tipo, descripción, sede, bloque de hallazgo, lugar, días atrás)
DEMO_OBJECTS = [
    ("Celular", "Celular negro con funda transparente y sticker de montaña", "Poblado", "Bloque A", "Cafetería, mesa junto a la ventana", 2),
    ("Billetera", "Billetera café de cuero con cremallera", "Poblado", "Bloque B", "Baño del segundo piso", 5),
    ("Audífonos inalámbricos", "Audífonos blancos en estuche con raya azul", "Sabaneta", "Bloque principal", "Auditorio, fila 3", 7),
    ("Carné universitario", "Carné universitario con cordón verde", "Poblado", "Bloque C", "Laboratorio de anatomía", 9),
    ("Chaqueta", "Chaqueta impermeable gris talla M", "Sabaneta", "Bloque principal", "Zona de mesas al aire libre", 12),
    ("Calculadora", "Calculadora científica con tapa negra", "Poblado", "Bloque A", "Salón 204", 3),
    ("Botella reutilizable", "Botella metálica rosada de 750 ml", "Poblado", "Bloque B", "Gimnasio", 4),
    ("Computador portátil", "Portátil gris de 14 pulgadas con calcomanías", "Poblado", "Bloque C", "Biblioteca, segundo piso", 1),
    ("Morral", "Morral azul oscuro con llavero de balón", "Sabaneta", "Bloque principal", "Parqueadero de motos", 6),
    ("Gafas formuladas", "Gafas de marco negro en estuche rojo", "Poblado", "Bloque A", "Sala de estudio", 8),
    ("Llavero", "Llavero con tres llaves y un destapador", "Poblado", "Bloque B", "Portería principal", 10),
    ("Estetoscopio", "Estetoscopio azul con iniciales grabadas", "Poblado", "Bloque C", "Simulación clínica", 11),
    ("Sombrilla", "Sombrilla negra plegable", "Sabaneta", "Bloque principal", "Entrada principal", 13),
    ("Cuaderno", "Cuaderno cuadriculado con portada de flores", "Poblado", "Bloque A", "Salón 101", 14),
    ("Cargador de portátil", "Cargador USB C de 65 W", "Poblado", "Bloque B", "Sala de cómputo", 15),
    ("Termo", "Termo plateado con tapa negra", "Sabaneta", "Bloque principal", "Cafetería", 16),
    ("Buzo", "Buzo verde con capota", "Poblado", "Bloque C", "Cancha", 18),
    ("Memoria USB", "Memoria USB de 64 GB con forma de llave", "Poblado", "Bloque A", "Sala de profesores", 20),
    ("Reloj inteligente", "Reloj inteligente con correa morada", "Sabaneta", "Bloque principal", "Gimnasio", 22),
    ("Tarjeta de transporte", "Tarjeta de transporte cívica", "Poblado", "Bloque B", "Fila de la cafetería", 24),
    ("Libro", "Libro de fisiología, edición 14", "Poblado", "Bloque C", "Biblioteca, mesa 8", 26),
    ("Casco de bicicleta", "Casco de bicicleta blanco con luces", "Sabaneta", "Bloque principal", "Cicloparqueadero", 28),
    ("Bata", "Bata blanca talla S con bordado", "Poblado", "Bloque A", "Vestier del laboratorio", 30),
    ("Gafas de sol", "Gafas de sol polarizadas", "Sabaneta", "Bloque principal", "Zona verde", 33),
]

COLORS = ["#2563eb", "#16a34a", "#dc2626", "#9333ea", "#ea580c", "#0891b2", "#4b5563", "#ca8a04"]


def make_demo_image(text, color):
    """Genera una imagen PNG sencilla (ficticia) para las fotos de demostración."""
    image = Image.new("RGB", (480, 320), color)
    draw = ImageDraw.Draw(image)
    draw.rectangle([20, 20, 460, 300], outline="white", width=4)
    draw.text((40, 140), text, fill="white")
    buffer = io.BytesIO()
    image.save(buffer, "PNG")
    return buffer.getvalue()


def get_role(name):
    return db.session.execute(select(Role).where(Role.name == name)).scalar_one()


def create_demo_user(email, full_name, identification, role_name, password):
    user = User(identification=identification, full_name=full_name, email=email,
                password_hash=generate_password_hash(password), role_id=get_role(role_name).id)
    db.session.add(user)
    db.session.flush()
    return user


def find_block(campus_name, block_name):
    return db.session.execute(
        select(Block).join(Campus).where(
            Campus.normalized_name == normalize_name(campus_name),
            Block.normalized_name == normalize_name(block_name)
        )
    ).scalar_one()


def run_demo_seed(password):
    exists = db.session.execute(
        select(User).where(User.email == "operador.demo@ces.test")
    ).scalar_one_or_none()
    if exists:
        return None

    admin = db.session.execute(
        select(User).join(Role).where(Role.name == ADMIN).order_by(User.id)
    ).scalars().first()
    if admin is None:
        raise RuntimeError("Primero ejecute python seed.py (crea roles, catálogos y el ADMIN).")

    operator = create_demo_user("operador.demo@ces.test", "Operador Demo", "DEMO-OP-01", OPERADOR, password)
    create_demo_user("consulta.demo@ces.test", "Consulta Demo", "DEMO-CO-01", CONSULTA, password)

    persons = []
    for identification, full_name, affiliation, department_name in DEMO_PERSONS:
        department = None
        if department_name:
            department = db.session.execute(
                select(Department).where(Department.normalized_name == normalize_name(department_name))
            ).scalar_one()
        person = Person(identification=identification, full_name=full_name, affiliation_type=affiliation,
                        department_id=department.id if department else None,
                        email=identification.lower() + "@demo.ces.test",
                        created_by=admin.id, updated_by=admin.id)
        db.session.add(person)
        db.session.flush()
        add_audit_log("person", person.id, "CREATE", admin.id, after=snapshot(person))
        persons.append(person)

    custody_poblado = find_block("Poblado", "Bloque A")
    custody_sabaneta = find_block("Sabaneta", "Bloque principal")
    now = utc_now()
    created = []

    for index, (type_name, description, campus_name, block_name, place, days_ago) in enumerate(DEMO_OBJECTS):
        object_type = db.session.execute(
            select(ObjectType).where(ObjectType.normalized_name == normalize_name(type_name))
        ).scalars().first()
        finder = persons[index % len(persons)]
        receiver = operator if index % 3 else admin
        received_at = now - timedelta(days=days_ago, hours=index % 5)
        object_id, code = next_object_code()
        custody = custody_sabaneta if campus_name == "Sabaneta" else custody_poblado
        object_lost = ObjectLost(
            id=object_id, code=code, object_type_id=object_type.id, description=description,
            found_block_id=find_block(campus_name, block_name).id, found_location=place,
            found_at=received_at - timedelta(hours=2),
            custody_block_id=custody.id, custody_location="Oficina de objetos perdidos, estante " + str(index % 4 + 1),
            finder_person_id=finder.id, finder_department_id=finder.department_id,
            received_by_user_id=receiver.id, received_at=received_at,
            status=DISPONIBLE, is_active=True, version=1,
            created_by=receiver.id, updated_by=receiver.id
        )
        db.session.add(object_lost)
        db.session.flush()
        add_audit_log("object_lost", object_lost.id, "CREATE", receiver.id, after=snapshot(object_lost))

        for photo_number in range(1 + index % 2):
            content = make_demo_image(f"{code} - {type_name} (foto {photo_number + 1})",
                                      COLORS[(index + photo_number) % len(COLORS)])
            photo = ObjectPhoto(object_lost_id=object_lost.id, storage_key=save_photo(content, "image/png"),
                                mime_type="image/png", size_bytes=len(content),
                                uploaded_by_user_id=receiver.id, uploaded_at=received_at,
                                updated_by=receiver.id)
            db.session.add(photo)
            db.session.flush()
            add_audit_log("object_photo", photo.id, "CREATE", receiver.id, after=snapshot(photo))
        created.append(object_lost)

    # 5 devueltos: reclamación aceptada + devolución con constancia
    for object_lost in created[:5]:
        owner = persons[(object_lost.id + 3) % len(persons)]
        claim = Claim(object_lost_id=object_lost.id, claimant_person_id=owner.id,
                      evidence="Describe marcas y contenido que no son visibles en las fotos.",
                      identity_verified=True, verification_notes="Documento de identidad verificado en ventanilla.",
                      status=ACEPTADA, reviewed_by=operator.id, reviewed_at=object_lost.received_at + timedelta(days=1),
                      decision_reason="La evidencia coincide con las características no públicas.",
                      created_by=operator.id, updated_by=operator.id)
        db.session.add(claim)
        db.session.flush()
        add_audit_log("claim", claim.id, "CREATE", operator.id, after=snapshot(claim))
        record = ReturnRecord(object_lost_id=object_lost.id, claim_id=claim.id, owner_person_id=owner.id,
                              delivered_by_user_id=operator.id,
                              returned_at=object_lost.received_at + timedelta(days=1, hours=1),
                              receipt_reference="CONST-" + object_lost.code.replace("OBJ-", ""),
                              receipt_method=RECEIPT_METHOD, owner_confirmation=True,
                              verification_summary="Identificación y características verificadas.")
        db.session.add(record)
        object_lost.status = DEVUELTO
        object_lost.version = 2
        db.session.flush()
        add_audit_log("return_record", record.id, "CREATE", operator.id, after=snapshot(record))

    # 2 inactivos por registro equivocado
    for object_lost, reason in zip(created[5:7], ["Registro duplicado por error del operador.",
                                                  "Se registró en una sede equivocada."]):
        object_lost.is_active = False
        object_lost.inactivated_at = object_lost.received_at + timedelta(hours=3)
        object_lost.inactivated_by = admin.id
        object_lost.inactivation_reason = reason
        object_lost.version = object_lost.version + 1
        add_audit_log("object_lost", object_lost.id, "INACTIVATE", admin.id, reason)

    # 2 reclamaciones pendientes y 1 rechazada (el objeto sigue DISPONIBLE)
    for object_lost, status in zip(created[7:10], [PENDIENTE, PENDIENTE, RECHAZADA]):
        claimant = persons[(object_lost.id + 5) % len(persons)]
        claim = Claim(object_lost_id=object_lost.id, claimant_person_id=claimant.id,
                      evidence="Dice que el objeto es suyo y describe su color.",
                      identity_verified=status != RECHAZADA, status=status,
                      created_by=operator.id, updated_by=operator.id)
        if status == RECHAZADA:
            claim.reviewed_by = operator.id
            claim.reviewed_at = utc_now()
            claim.decision_reason = "La descripción no coincide con las características no públicas."
        db.session.add(claim)
        db.session.flush()
        add_audit_log("claim", claim.id, "CREATE", operator.id, after=snapshot(claim))

    db.session.commit()
    return {"objects": len(created), "returned": 5, "inactive": 2, "persons": len(persons)}
