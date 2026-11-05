from datetime import datetime, timezone
from app.extensions import db


class TokenRevocation(db.Model):
    """JWT revocados con logout. Si el jti de un token está aquí, el token se rechaza."""
    __tablename__ = "token_revocations"

    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(64), nullable=False, unique=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    revoked_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
