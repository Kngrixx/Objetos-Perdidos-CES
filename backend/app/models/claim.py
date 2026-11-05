from datetime import datetime, timezone
from app.extensions import db


class Claim(db.Model):
    """Reclamación de un objeto por parte de una persona que dice ser su propietaria."""
    __tablename__ = "claims"

    id = db.Column(db.Integer, primary_key=True)
    object_lost_id = db.Column(
        db.Integer,
        db.ForeignKey("object_lost.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    claimant_person_id = db.Column(
        db.Integer,
        db.ForeignKey("persons.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    # Evidencia de pertenencia y verificación (características no públicas, identificación).
    evidence = db.Column(db.Text, nullable=False)
    identity_verified = db.Column(db.Boolean, nullable=False, default=False)
    verification_notes = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(20), nullable=False, default="PENDIENTE", index=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    decision_reason = db.Column(db.Text, nullable=True)
    correction_reason = db.Column(db.Text, nullable=True)
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
    created_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    inactivated_at = db.Column(db.DateTime(timezone=True), nullable=True)
    inactivated_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    inactivation_reason = db.Column(db.Text, nullable=True)

    object_lost = db.relationship("ObjectLost")
    claimant = db.relationship("Person", foreign_keys=[claimant_person_id])
    reviewer = db.relationship("User", foreign_keys=[reviewed_by])

    __table_args__ = (
        db.CheckConstraint("status IN ('PENDIENTE', 'ACEPTADA', 'RECHAZADA')", name="ck_claims_status"),
        # Índice único PARCIAL: a lo sumo una reclamación ACEPTADA por objeto.
        # Las PENDIENTES y RECHAZADAS no cuentan, por eso no es un UNIQUE normal.
        db.Index(
            "uq_claims_one_accepted_per_object",
            "object_lost_id",
            unique=True,
            postgresql_where=db.text("status = 'ACEPTADA'")
        ),
    )
