import logging
import uuid
from decimal import Decimal, InvalidOperation

import requests
from flask import Flask, jsonify, request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("mock_payment")

app = Flask(__name__)
SUCCESS_STATUS = "COMPLETED"


@app.get("/health")
def health():
    return {"status": "ok"}, 200


@app.post("/payments")
def create_payment():
    data = request.get_json(silent=True) or {}
    booking_id = data.get("booking_id")
    amount = data.get("amount")
    webhook_url = data.get("webhook_url")

    if booking_id is None or amount is None or not webhook_url:
        return jsonify(
            {"error": "booking_id, amount and webhook_url are required"}
        ), 400

    try:
        booking_id = int(booking_id)
    except (TypeError, ValueError):
        return jsonify({"error": "booking_id must be an integer"}), 400

    try:
        amount = Decimal(str(amount))
    except (InvalidOperation, TypeError, ValueError):
        return jsonify({"error": "amount must be a valid number"}), 400

    if amount <= 0:
        return jsonify({"error": "amount must be greater than zero"}), 400

    payment_id = f"pay_{uuid.uuid4().hex[:12]}"
    status = SUCCESS_STATUS

    # The mock service is the source of the payment event and calls the
    # merchant webhook using requests, just like an external provider would.
    webhook_payload = {
        "payment_id": payment_id,
        "booking_id": booking_id,
        "status": status,
    }

    try:
        webhook_response = requests.post(
            webhook_url,
            json=webhook_payload,
            timeout=5,
        )
        webhook_response.raise_for_status()
    except requests.RequestException:
        logger.exception("Failed to deliver webhook for payment_id=%s", payment_id)
        return {"error": "Webhook delivery failed", "payment_id": payment_id}, 502

    logger.info(
        "Mock payment processed payment_id=%s booking_id=%s status=%s",
        payment_id,
        booking_id,
        status,
    )

    return jsonify(
        {
            "payment_id": payment_id,
            "booking_id": booking_id,
            "amount": str(amount.quantize(Decimal("0.01"))),
            "status": status,
        }
    ), 201


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
