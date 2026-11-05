from datetime import datetime, timezone
from app.extensions import db


class Person(db.Model):
    """Persona externa al login: entrega o reclama objetos sin tener cuenta."""
    __tablename__ = "persons"

    id = db.Column(db.Integer, primary_key=True)
    # Texto (no número): hay documentos con letras o ceros a la izquierda.
    identification = db.Column(db.String(30), nullable=False, unique=True)
    full_name = db.Column(db.String(150), nullable=False)
    affiliation_type = db.Column(db.String(20), nullable=False)
    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=True,
        index=True
    )
    email = db.Column(db.String(200), nullable=True)
    phone = db.Column(db.String(30), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    created_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    inactivated_at = db.Column(db.DateTime(timezone=True), nullable=True)
    inactivated_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    inactivation_reason = db.Column(db.Text, nullable=True)

    department = db.relationship("Department")

    __table_args__ = (
        db.CheckConstraint(
            "affiliation_type IN ('ESTUDIANTE', 'EMPLEADO', 'CONTRATISTA', 'PROVEEDOR', 'VISITANTE')",
            name="ck_persons_affiliation_type"
        ),
    )
