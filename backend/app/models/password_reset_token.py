from datetime import datetime, timezone
from app.extensions import db


class PasswordResetToken(db.Model):
    """Token de recuperación: se guarda solo su HASH, vence a los 15 minutos y es de un solo uso.
    El registro nunca se borra: used_at y revoked_at dejan el historial."""
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    token_hash = db.Column(db.String(64), nullable=False, unique=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    used_at = db.Column(db.DateTime(timezone=True), nullable=True)
    revoked_at = db.Column(db.DateTime(timezone=True), nullable=True)
