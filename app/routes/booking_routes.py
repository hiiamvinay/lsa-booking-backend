from datetime import datetime
from decimal import Decimal
from flask import Blueprint, jsonify, request, current_app
from app.extensions import db
from app.models.booking import BookingRequest
from app.models.lsa import LSAProfile
from app.models.parent import Parent
from app.models.payment import Payment
from app.services.payment import create_payment, PaymentServiceError
import logging

logger = logging.getLogger(__name__)

booking_bp = Blueprint("booking", __name__)

CONFLICT_STATUSES = {"PENDING", "COMPLETED"}


def error_response(message, status_code):
    response = jsonify({"error": message})
    response.status_code = status_code
    return response


def parse_iso_datetime(value, field_name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"'{field_name}' must be a non-empty ISO 8601 datetime string.")

    normalized_value = value.strip().replace("Z", "+00:00")

    try:
        parsed = datetime.fromisoformat(normalized_value)
    except ValueError as exc:
        raise ValueError(f"'{field_name}' must be a valid ISO 8601 datetime.") from exc

    if parsed.tzinfo is None:
        raise ValueError(f"'{field_name}' must include timezone information.")

    return parsed

def calculate_amount(lsa, start_time, end_time):
    hours = Decimal(str((end_time - start_time).total_seconds())) / Decimal("3600")
    return (Decimal(lsa.hourly_rate) * hours).quantize(Decimal("0.01"))

def serialize_booking(booking):
    return {
        "id": booking.id,
        "parent_id": booking.parent_id,
        "lsa_id": booking.lsa_id,
        "status": booking.status,
        "start_time": booking.start_time.isoformat(),
        "end_time": booking.end_time.isoformat(),
        "created_at": booking.created_at.isoformat(),
        "parent": {
            "id": booking.parent.id,
            "name": booking.parent.name,
            "email": booking.parent.email,
            "phone": booking.parent.phone,
        },
        "lsa": {
            "id": booking.lsa.id,
            "name": booking.lsa.name,
            "email": booking.lsa.email,
            "hourly_rate": float(booking.lsa.hourly_rate),
            "is_active": booking.lsa.is_active,
        },
    }


@booking_bp.post("/bookings")
def create_booking():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error_response("Request body must be a valid JSON object.", 400)

    missing_fields = [
        field for field in ("parent_id", "lsa_id", "start_time", "end_time")
        if field not in payload
    ]
    if missing_fields:
        return error_response(
            f"Missing required field(s): {', '.join(missing_fields)}.",
            400
        )

    try:
        parent_id = int(payload["parent_id"])
        lsa_id = int(payload["lsa_id"])
        start_time = parse_iso_datetime(payload["start_time"], "start_time")
        end_time = parse_iso_datetime(payload["end_time"], "end_time")
    except (TypeError, ValueError) as exc:
        return error_response(str(exc), 400)

    if end_time <= start_time:
        return error_response("'end_time' must be later than 'start_time'.", 400)

    parent = db.session.get(Parent, parent_id)
    if parent is None:
        return error_response("Parent not found.", 404)

    lsa = db.session.get(LSAProfile, lsa_id)
    if lsa is None:
        return error_response("LSA not found.", 404)

    if not lsa.is_active:
        return error_response("Bookings cannot be created for an inactive LSA.", 409)

    overlapping_booking = (
        BookingRequest.query.filter(
            BookingRequest.lsa_id == lsa_id,
            BookingRequest.status.in_(CONFLICT_STATUSES),
            BookingRequest.start_time < end_time,
            BookingRequest.end_time > start_time,
        )
        .order_by(BookingRequest.start_time.asc())
        .first()
    )

    if overlapping_booking is not None:
        return error_response("The selected LSA is already booked for that time range.", 409)

    booking = BookingRequest(
        parent_id=parent_id,
        lsa_id=lsa_id,
        start_time=start_time,
        end_time=end_time,
        status="PENDING",
    )

    amount = calculate_amount(lsa, start_time, end_time)    
    print(f"Calculated amount: {amount}")
    db.session.add(booking)
    db.session.flush()

    payment = Payment(
        booking_id=booking.id,
        amount=amount,
        status="PENDING",
    )
    

    db.session.add(payment)
    db.session.commit()

    try:
        payment_result = create_payment(
            current_app.config["PAYMENT_SERVICE_URL"],
            current_app.config["PAYMENT_WEBHOOK_URL"],
            booking.id,
            amount,
        )
    except PaymentServiceError as exc:
        logger.error("Payment initiation failed for booking_id=%s", booking.id)
        payment.status = "FAILED"
        booking.status = "FAILED"
        db.session.commit()
        return {
            "error": {
                "code": "PAYMENT_SERVICE_ERROR",
                "message": str(exc),
                "booking_id": booking.id,
            }
        }, 502


    db.session.refresh(payment)
    db.session.refresh(booking)

    return {
        "data": {
            "booking_id": booking.id,
            "booking_status": booking.status,
            "payment": {
                "payment_id": payment.id,
                "external_payment_id": payment.external_payment_id,
                "amount": float(payment.amount),
                    "payment_status": payment.status,
                },
        }
    }, 201
    

    


@booking_bp.get("/bookings/<int:booking_id>")
def get_booking(booking_id):
    booking = db.session.get(BookingRequest, booking_id)
    if booking is None:
        return error_response("Booking not found.", 404)

    return jsonify({"data": serialize_booking(booking)})
