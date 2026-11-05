from datetime import datetime, timezone
from app.extensions import db


class ObjectType(db.Model):
    """Tipo reutilizable del catálogo (por ejemplo, "Celular"). No es un objeto físico."""
    __tablename__ = "object_types"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("object_categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    name = db.Column(db.String(100), nullable=False)
    normalized_name = db.Column(db.String(100), nullable=False)
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

    category = db.relationship("ObjectCategory", back_populates="object_types")

    __table_args__ = (
        # Impide duplicados concurrentes: nombre normalizado único dentro de cada categoría.
        db.UniqueConstraint("category_id", "normalized_name", name="uq_object_types_category_normalized_name"),
    )
