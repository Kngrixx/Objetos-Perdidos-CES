from datetime import datetime, timezone
from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    identification = db.Column(db.String(50), nullable=False, unique=True)
    full_name = db.Column(db.String(150), nullable=False)
    # Se guarda normalizado (minúsculas, sin espacios) para que el UNIQUE no distinga mayúsculas.
    email = db.Column(db.String(200), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role_id = db.Column(
        db.Integer,
        db.ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    # Se incrementa al cambiar o restablecer la contraseña y al inactivar:
    # los JWT emitidos antes dejan de servir.
    token_version = db.Column(db.Integer, nullable=False, default=0)

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

    role = db.relationship("Role", back_populates="users")
