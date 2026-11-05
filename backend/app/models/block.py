from datetime import datetime, timezone
from app.extensions import db


class Block(db.Model):
    __tablename__ = "blocks"

    id = db.Column(db.Integer, primary_key=True)
    campus_id = db.Column(
        db.Integer,
        db.ForeignKey("campuses.id", ondelete="RESTRICT"),
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

    campus = db.relationship("Campus", back_populates="blocks")

    __table_args__ = (
        # El nombre del bloque es único DENTRO de su sede.
        db.UniqueConstraint("campus_id", "normalized_name", name="uq_blocks_campus_normalized_name"),
    )
