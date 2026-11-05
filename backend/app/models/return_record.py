from datetime import datetime, timezone
from app.extensions import db


class ReturnRecord(db.Model):
    """Histórico de devolución (solo lectura). Una sola devolución por objeto y por reclamación."""
    __tablename__ = "return_records"

    id = db.Column(db.Integer, primary_key=True)
    # UNIQUE: garantía de la base de datos contra una segunda devolución del mismo objeto.
    object_lost_id = db.Column(
        db.Integer,
        db.ForeignKey("object_lost.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True
    )
    claim_id = db.Column(
        db.Integer,
        db.ForeignKey("claims.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True
    )
    owner_person_id = db.Column(
        db.Integer,
        db.ForeignKey("persons.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    delivered_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )
    returned_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    receipt_reference = db.Column(db.String(30), nullable=False, unique=True)
    receipt_method = db.Column(db.String(30), nullable=False, default="CONFIRMACION_DIGITAL")
    owner_confirmation = db.Column(db.Boolean, nullable=False)
    verification_summary = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    object_lost = db.relationship("ObjectLost")
    claim = db.relationship("Claim")
    owner = db.relationship("Person", foreign_keys=[owner_person_id])
    delivered_by = db.relationship("User", foreign_keys=[delivered_by_user_id])

    __table_args__ = (
        db.CheckConstraint("owner_confirmation = TRUE", name="ck_return_records_owner_confirmation"),
    )
