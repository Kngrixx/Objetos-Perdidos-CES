from datetime import datetime, timezone
from app.extensions import db


class ObjectLost(db.Model):
    """Un objeto físico concreto recibido en custodia (una unidad por registro)."""
    __tablename__ = "object_lost"

    id = db.Column(db.Integer, primary_key=True)
    # Código único generado por el servidor, por ejemplo OBJ-000015.
    code = db.Column(db.String(20), nullable=False, unique=True)
    object_type_id = db.Column(
        db.Integer,
        db.ForeignKey("object_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    description = db.Column(db.Text, nullable=False)

    # Hallazgo (la sede se obtiene del bloque)
    found_block_id = db.Column(
        db.Integer,
        db.ForeignKey("blocks.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    found_location = db.Column(db.String(255), nullable=False)
    found_at = db.Column(db.DateTime(timezone=True), nullable=False)

    # Custodia (puede ser distinta al lugar del hallazgo)
    custody_block_id = db.Column(
        db.Integer,
        db.ForeignKey("blocks.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    custody_location = db.Column(db.String(255), nullable=False)

    # Quién entrega y quién recibe
    finder_person_id = db.Column(
        db.Integer,
        db.ForeignKey("persons.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    finder_department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=True
    )
    received_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )
    received_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )

    # Control: status = situación del objeto; is_active = validez del registro.
    status = db.Column(db.String(20), nullable=False, default="DISPONIBLE", index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, index=True)
    # Bloqueo optimista: cada edición debe enviar la versión que leyó.
    version = db.Column(db.Integer, nullable=False, default=1)
    correction_reason = db.Column(db.Text, nullable=True)

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
    created_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    inactivated_at = db.Column(db.DateTime(timezone=True), nullable=True)
    inactivated_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    inactivation_reason = db.Column(db.Text, nullable=True)

    object_type = db.relationship("ObjectType")
    found_block = db.relationship("Block", foreign_keys=[found_block_id])
    custody_block = db.relationship("Block", foreign_keys=[custody_block_id])
    finder_person = db.relationship("Person", foreign_keys=[finder_person_id])
    finder_department = db.relationship("Department", foreign_keys=[finder_department_id])
    received_by = db.relationship("User", foreign_keys=[received_by_user_id])
    photos = db.relationship("ObjectPhoto", back_populates="object_lost", order_by="ObjectPhoto.id")

    __table_args__ = (
        db.CheckConstraint("status IN ('DISPONIBLE', 'DEVUELTO')", name="ck_object_lost_status"),
        db.CheckConstraint("version >= 1", name="ck_object_lost_version"),
        db.CheckConstraint("found_at <= received_at", name="ck_object_lost_found_before_received"),
        db.Index("ix_object_lost_status_is_active", "status", "is_active"),
    )
