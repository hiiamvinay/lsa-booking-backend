import os
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app import create_app
from app.extensions import db
from app.models.booking import BookingRequest
from app.models.lsa import LSAProfile
from app.models.parent import Parent
from app.models.payment import Payment
from app.models.skill import Skill
from app.routes import booking_routes
from app.services.payment import PaymentServiceError


@pytest.fixture
def app():
    os.environ["FLASK_CONFIG"] = "testing"
    app = create_app("testing")

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seed_data(app):
    with app.app_context():
        reading = Skill(name="Reading Support")
        autism = Skill(name="Autism")

        active_lsa = LSAProfile(
            name="Amit Kumar",
            email="amit.lsa@example.com",
            hourly_rate=Decimal("800.00"),
            is_active=True,
        )
        active_lsa.skills = [reading, autism]

        inactive_lsa = LSAProfile(
            name="Sneha Patel",
            email="sneha.lsa@example.com",
            hourly_rate=Decimal("850.00"),
            is_active=False,
        )
        inactive_lsa.skills = [autism]

        parent = Parent(
            name="Rahul Sharma",
            email="rahul@example.com",
            phone="9876543210",
        )

        db.session.add_all([parent, active_lsa, inactive_lsa])
        db.session.commit()

        return {
            "parent_id": parent.id,
            "active_lsa_id": active_lsa.id,
            "inactive_lsa_id": inactive_lsa.id,
        }


def create_booking_and_payment(
    app,
    seed_data,
    *,
    booking_status="PENDING",
    payment_status="PENDING",
    external_payment_id=None,
):
    with app.app_context():
        booking = BookingRequest(
            parent_id=seed_data["parent_id"],
            lsa_id=seed_data["active_lsa_id"],
            start_time=datetime(2026, 8, 10, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 8, 10, 11, 0, tzinfo=timezone.utc),
            status=booking_status,
        )
        db.session.add(booking)
        db.session.flush()

        payment = Payment(
            booking_id=booking.id,
            amount=Decimal("800.00"),
            status=payment_status,
            external_payment_id=external_payment_id,
        )
        db.session.add(payment)
        db.session.commit()

        return booking.id, payment.id


def test_get_lsas_returns_only_active_lsas_by_default(client, seed_data):
    response = client.get("/api/lsas/search")


    assert response.status_code == 200
    payload = response.get_json()

    assert payload["count"] == 1
    assert payload["data"][0]["id"] == seed_data["active_lsa_id"]
    assert payload["data"][0]["is_active"] is True


def test_post_bookings_completes_booking_when_payment_completes(app, client, seed_data, monkeypatch):
    def fake_create_payment(payment_service_url, webhook_url, booking_id, amount):
        assert payment_service_url == app.config["PAYMENT_SERVICE_URL"]
        assert webhook_url == app.config["PAYMENT_WEBHOOK_URL"]
        assert amount == Decimal("800.00")

        webhook_client = app.test_client()
        webhook_response = webhook_client.post(
            "/api/payments/webhook",
            json={
                "payment_id": "pay_completed_001",
                "booking_id": booking_id,
                "status": "COMPLETED",
            },
        )

        assert webhook_response.status_code == 200
        return {
            "payment_id": "pay_completed_001",
            "booking_id": booking_id,
            "amount": "800.00",
            "status": "COMPLETED",
        }

    monkeypatch.setattr(booking_routes, "create_payment", fake_create_payment)

    response = client.post(
        "/bookings",
        json={
            "parent_id": seed_data["parent_id"],
            "lsa_id": seed_data["active_lsa_id"],
            "start_time": "2026-08-10T10:00:00+00:00",
            "end_time": "2026-08-10T11:00:00+00:00",
        },
    )

    assert response.status_code == 201
    payload = response.get_json()["data"]

    assert payload["booking_status"] == "COMPLETED"
    assert payload["payment"]["payment_status"] == "COMPLETED"
    assert payload["payment"]["external_payment_id"] == "pay_completed_001"

    with app.app_context():
        booking = db.session.get(BookingRequest, payload["booking_id"])
        payment = db.session.get(Payment, payload["payment"]["payment_id"])
        assert booking.status == "COMPLETED"
        assert payment.status == "COMPLETED"


def test_post_bookings_marks_booking_failed_when_payment_service_fails(
    app, client, seed_data, monkeypatch
):
    def fake_create_payment(*args, **kwargs):
        raise PaymentServiceError("Payment service is unavailable")

    monkeypatch.setattr(booking_routes, "create_payment", fake_create_payment)

    response = client.post(
        "/bookings",
        json={
            "parent_id": seed_data["parent_id"],
            "lsa_id": seed_data["active_lsa_id"],
            "start_time": "2026-08-10T12:00:00+00:00",
            "end_time": "2026-08-10T13:00:00+00:00",
        },
    )

    assert response.status_code == 502
    payload = response.get_json()["error"]

    assert payload["code"] == "PAYMENT_SERVICE_ERROR"
    assert payload["message"] == "Payment service is unavailable"

    with app.app_context():
        booking = db.session.get(BookingRequest, payload["booking_id"])
        payment = db.session.scalar(
            db.select(Payment).where(Payment.booking_id == payload["booking_id"])
        )
        assert booking.status == "FAILED"
        assert payment.status == "FAILED"


def test_post_bookings_rejects_overlap_with_completed_booking(app, client, seed_data):
    create_booking_and_payment(app, seed_data, booking_status="COMPLETED", payment_status="COMPLETED")

    response = client.post(
        "/bookings",
        json={
            "parent_id": seed_data["parent_id"],
            "lsa_id": seed_data["active_lsa_id"],
            "start_time": "2026-08-10T10:30:00+00:00",
            "end_time": "2026-08-10T11:30:00+00:00",
        },
    )

    assert response.status_code == 409
    assert response.get_json()["error"] == "The selected LSA is already booked for that time range."


def test_payment_webhook_marks_booking_and_payment_completed(app, client, seed_data):
    booking_id, payment_id = create_booking_and_payment(app, seed_data)

    response = client.post(
        "/api/payments/webhook",
        json={
            "payment_id": "pay_webhook_success",
            "booking_id": booking_id,
            "status": "COMPLETED",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["booking_status"] == "COMPLETED"
    assert payload["payment_status"] == "COMPLETED"

    with app.app_context():
        booking = db.session.get(BookingRequest, booking_id)
        payment = db.session.get(Payment, payment_id)
        assert booking.status == "COMPLETED"
        assert payment.status == "COMPLETED"
        assert payment.external_payment_id == "pay_webhook_success"


def test_payment_webhook_marks_booking_and_payment_failed(app, client, seed_data):
    booking_id, payment_id = create_booking_and_payment(app, seed_data)

    response = client.post(
        "/api/payments/webhook",
        json={
            "payment_id": "pay_webhook_failed",
            "booking_id": booking_id,
            "status": "FAILED",
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["booking_status"] == "FAILED"
    assert payload["payment_status"] == "FAILED"

    with app.app_context():
        booking = db.session.get(BookingRequest, booking_id)
        payment = db.session.get(Payment, payment_id)
        assert booking.status == "FAILED"
        assert payment.status == "FAILED"
        assert payment.external_payment_id == "pay_webhook_failed"


def test_payment_webhook_is_idempotent_for_completed_status(app, client, seed_data):
    booking_id, payment_id = create_booking_and_payment(
        app,
        seed_data,
        booking_status="COMPLETED",
        payment_status="COMPLETED",
        external_payment_id="pay_repeat",
    )

    response = client.post(
        "/api/payments/webhook",
        json={
            "payment_id": "pay_repeat",
            "booking_id": booking_id,
            "status": "COMPLETED",
        },
    )

    assert response.status_code == 200
    assert response.get_json()["message"] == "Webhook already processed"

    with app.app_context():
        booking = db.session.get(BookingRequest, booking_id)
        payment = db.session.get(Payment, payment_id)
        assert booking.status == "COMPLETED"
        assert payment.status == "COMPLETED"


def test_payment_webhook_rejects_missing_fields(client):
    response = client.post(
        "/api/payments/webhook",
        json={
            "payment_id": "pay_missing_fields",
        },
    )

    assert response.status_code == 400
    payload = response.get_json()["error"]
    assert payload["code"] == "VALIDATION_ERROR"
    assert "booking_id, status" in payload["message"]


def test_payment_webhook_rejects_unsupported_status_without_changing_records(
    app, client, seed_data
):
    booking_id, payment_id = create_booking_and_payment(app, seed_data)

    response = client.post(
        "/api/payments/webhook",
        json={
            "payment_id": "pay_processing",
            "booking_id": booking_id,
            "status": "PROCESSING",
        },
    )

    assert response.status_code == 400
    payload = response.get_json()["error"]
    assert payload["code"] == "INVALID_PAYMENT_STATUS"

    with app.app_context():
        booking = db.session.get(BookingRequest, booking_id)
        payment = db.session.get(Payment, payment_id)
        assert booking.status == "PENDING"
        assert payment.status == "PENDING"


def test_payment_webhook_returns_404_when_payment_record_is_missing(app, client, seed_data):
    with app.app_context():
        booking = BookingRequest(
            parent_id=seed_data["parent_id"],
            lsa_id=seed_data["active_lsa_id"],
            start_time=datetime(2026, 8, 10, 10, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 8, 10, 11, 0, tzinfo=timezone.utc),
            status="PENDING",
        )
        db.session.add(booking)
        db.session.commit()
        booking_id = booking.id

    response = client.post(
        "/api/payments/webhook",
        json={
            "payment_id": "pay_missing_payment",
            "booking_id": booking_id,
            "status": "COMPLETED",
        },
    )

    assert response.status_code == 404
    payload = response.get_json()["error"]
    assert payload["code"] == "PAYMENT_NOT_FOUND"
