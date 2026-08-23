from datetime import datetime, timezone
from app.extensions import db


class Parent(db.Model):
    __tablename__ = "parents"

    id = db.Column(db.Integer, primary_key=True)

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

    phone = db.Column(
        db.String(20),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    bookings = db.relationship(
        "BookingRequest",
        back_populates="parent"
    )

    def __repr__(self):
        return f"<Parent {self.id}: {self.email}>"