from datetime import datetime, timezone
from app.extensions import db


class AuditLog(db.Model):
    """Historial de cambios. Solo inserción y consulta (un trigger impide UPDATE y DELETE).
    Nunca guarda contraseñas, tokens, archivos ni secretos."""
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    entity = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(50), nullable=False)
    actor_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True
    )
    occurred_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
    reason = db.Column(db.Text, nullable=True)
    before_data = db.Column(db.JSON, nullable=True)
    after_data = db.Column(db.JSON, nullable=True)

    actor = db.relationship("User", foreign_keys=[actor_user_id])

    __table_args__ = (
        db.Index("ix_audit_logs_entity_entity_id", "entity", "entity_id"),
    )
