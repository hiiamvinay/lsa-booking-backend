from datetime import datetime, timezone

from app.extensions import db


class LSAProfile(db.Model):
    __tablename__ = "lsa_profiles"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(255),
        nullable=False,
        unique=True,
        index=True
    )

    hourly_rate = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        index=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    skills = db.relationship(
        "Skill",
        secondary="lsa_skills",
        back_populates="lsas"
    )

    bookings = db.relationship(
        "BookingRequest",
        back_populates="lsa",
    )

    def __repr__(self):
        return f"<LSAProfile {self.id}: {self.name}>"