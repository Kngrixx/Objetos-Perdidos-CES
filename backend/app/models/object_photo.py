from datetime import datetime, timezone
from app.extensions import db


class ObjectPhoto(db.Model):
    """Metadata de una fotografía. El archivo vive en disco; aquí solo la referencia."""
    __tablename__ = "object_photos"

    id = db.Column(db.Integer, primary_key=True)
    object_lost_id = db.Column(
        db.Integer,
        db.ForeignKey("object_lost.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    # Nombre interno generado por el servidor (nunca el nombre que envió el usuario).
    storage_key = db.Column(db.String(100), nullable=False, unique=True)
    mime_type = db.Column(db.String(20), nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False)
    uploaded_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )
    uploaded_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    inactivated_at = db.Column(db.DateTime(timezone=True), nullable=True)
    inactivated_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    inactivation_reason = db.Column(db.Text, nullable=True)

    object_lost = db.relationship("ObjectLost", back_populates="photos")
    uploaded_by = db.relationship("User", foreign_keys=[uploaded_by_user_id])

    __table_args__ = (
        db.CheckConstraint("mime_type IN ('image/jpeg', 'image/png')", name="ck_object_photos_mime_type"),
        db.CheckConstraint("size_bytes > 0 AND size_bytes <= 5242880", name="ck_object_photos_size"),
    )
