import logging

import requests

logger = logging.getLogger(__name__)


class PaymentServiceError(Exception):
    """Raised when the external payment service cannot be used."""


def create_payment(payment_service_url, webhook_url, booking_id, amount):
    url = f"{payment_service_url.rstrip('/')}/payments"
    payload = {
        "booking_id": booking_id,
        "amount": float(amount),
        "webhook_url": webhook_url,
    }

    try:
        logger.info("Starting payment request for booking_id=%s", booking_id)
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        data = response.json()

        logger.info(
            "Payment service accepted booking_id=%s payment_id=%s status=%s",
            booking_id,
            data.get("payment_id"),
            data.get("status"),
        )
        return data

    except requests.Timeout as exc:
        logger.error("Payment service timeout for booking_id=%s", booking_id)
        raise PaymentServiceError("Payment service timed out") from exc
    except requests.ConnectionError as exc:
        logger.error("Payment service unavailable for booking_id=%s", booking_id)
        raise PaymentServiceError("Payment service is unavailable") from exc
    except requests.HTTPError as exc:
        logger.error(
            "Payment service HTTP error for booking_id=%s status=%s",
            booking_id,
            exc.response.status_code if exc.response is not None else "unknown",
        )
        raise PaymentServiceError("Payment service returned an HTTP error") from exc
    except (requests.RequestException, ValueError) as exc:
        logger.error("Payment service request failed for booking_id=%s", booking_id)
        raise PaymentServiceError("Payment service request failed") from exc