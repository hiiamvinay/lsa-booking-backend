from datetime import datetime, timezone

from app.extensions import db


class BookingRequest(db.Model):
    __tablename__ = "booking_requests"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    parent_id = db.Column(
        db.Integer,
        db.ForeignKey("parents.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    lsa_id = db.Column(
        db.Integer,
        db.ForeignKey("lsa_profiles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )

    start_time = db.Column(
        db.DateTime(timezone=True),
        nullable=False
    )

    end_time = db.Column(
        db.DateTime(timezone=True),
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="PENDING",
        index=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    parent = db.relationship(
        "Parent",
        back_populates="bookings"
    )

    lsa = db.relationship(
        "LSAProfile",
        back_populates="bookings"
    )
    payment = db.relationship(
        "Payment",
        back_populates="booking",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        db.Index(
            "ix_booking_lsa_time",
            "lsa_id",
            "start_time",
            "end_time"
        ),
    )

    def __repr__(self):
        return f"<BookingRequest {self.id}: {self.status}>"