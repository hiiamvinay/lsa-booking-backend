import logging

from flask import Blueprint, request

from app.extensions import db
from app.models.booking import BookingRequest
from app.models.payment import Payment


logger = logging.getLogger(__name__)
payments_bp = Blueprint("payments", __name__, url_prefix="/api/payments")
PROVIDER_SUCCESS_STATUSES = {"COMPLETED", "SUCCESS"}
PROVIDER_FAILED_STATUSES = {"FAILED"}


@payments_bp.post("/webhook", strict_slashes=False)
def payment_webhook():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return {"error": {"code": "INVALID_JSON", "message": "JSON body is required"}}, 400

    required = {"payment_id", "booking_id", "status"}
    missing = sorted(required - data.keys())
    if missing:
        return {
            "error": {
                "code": "VALIDATION_ERROR",
                "message": f"Missing fields: {', '.join(missing)}",
            }
        }, 400

    try:
        booking_id = int(data["booking_id"])
    except (TypeError, ValueError):
        return {"error": {"code": "VALIDATION_ERROR", "message": "Invalid booking_id"}}, 400

    payment = db.session.scalar(
        db.select(Payment)
        .where(Payment.external_payment_id == data["payment_id"])
        .with_for_update()
    )

    booking = db.session.get(BookingRequest, booking_id, with_for_update=True)

    if booking is None:
        return {"error": {"code": "BOOKING_NOT_FOUND", "message": "Booking not found"}}, 404

    if payment is None:
        payment = db.session.scalar(
            db.select(Payment)
            .where(Payment.booking_id == booking_id)
            .with_for_update()
        )

    if payment is None:
        return {"error": {"code": "PAYMENT_NOT_FOUND", "message": "Payment not found"}}, 404

    provider_status = str(data["status"]).strip().upper()

    # Idempotency: a repeated webhook for the same final state is harmless.
    if payment.status == "COMPLETED" and provider_status in PROVIDER_SUCCESS_STATUSES:
        return {"message": "Webhook already processed"}, 200
    if payment.status == "FAILED" and provider_status in PROVIDER_FAILED_STATUSES:
        return {"message": "Webhook already processed"}, 200

    payment.external_payment_id = data["payment_id"]

    if provider_status in PROVIDER_SUCCESS_STATUSES:
        payment.status = "COMPLETED"
        booking.status = "COMPLETED"
    elif provider_status in PROVIDER_FAILED_STATUSES:
        payment.status = "FAILED"
        booking.status = "FAILED"
    else:
        return {
            "error": {"code": "INVALID_PAYMENT_STATUS", "message": "Unsupported payment status"}
        }, 400

    db.session.commit()

    logger.info(
        "Payment webhook processed payment_id=%s booking_id=%s status=%s",
        data["payment_id"],
        booking.id,
        data["status"],
    )

    return {
        "message": "Webhook processed",
        "booking_id": booking.id,
        "booking_status": booking.status,
        "payment_status": payment.status,
    }, 200
