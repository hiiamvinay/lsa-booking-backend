import unittest
from datetime import datetime, timezone
from decimal import Decimal

from app import create_app
from app.extensions import db
from app.models.booking import BookingRequest
from app.models.lsa import LSAProfile
from app.models.parent import Parent
from app.models.skill import Skill


class RoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            }
        )
        
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            self.seed_data()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def seed_data(self):
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

        self.parent_id = parent.id
        self.active_lsa_id = active_lsa.id
        self.inactive_lsa_id = inactive_lsa.id
        self.reading_skill_id = reading.id

    def test_get_lsas_returns_only_active_lsas_by_default(self):
        response = self.client.get("/lsas")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["data"][0]["id"], self.active_lsa_id)
        self.assertTrue(payload["data"][0]["is_active"])

    def test_get_lsas_filters_by_skill_name(self):
        response = self.client.get("/lsas?skill=Reading%20Support")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["data"][0]["id"], self.active_lsa_id)
        self.assertEqual(
            [skill["name"] for skill in payload["data"][0]["skills"]],
            ["Autism", "Reading Support"],
        )

    def test_post_bookings_creates_booking(self):
        response = self.client.post(
            "/bookings",
            json={
                "parent_id": self.parent_id,
                "lsa_id": self.active_lsa_id,
                "start_time": "2026-08-10T10:00:00+00:00",
                "end_time": "2026-08-10T11:00:00+00:00",
            },
        )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()["data"]

        self.assertEqual(payload["parent_id"], self.parent_id)
        self.assertEqual(payload["lsa_id"], self.active_lsa_id)
        self.assertEqual(payload["status"], "PENDING")

        with self.app.app_context():
            self.assertEqual(BookingRequest.query.count(), 1)

    def test_post_bookings_rejects_overlapping_booking(self):
        with self.app.app_context():
            existing_booking = BookingRequest(
                parent_id=self.parent_id,
                lsa_id=self.active_lsa_id,
                start_time=datetime(2026, 8, 10, 10, 0, tzinfo=timezone.utc),
                end_time=datetime(2026, 8, 10, 11, 0, tzinfo=timezone.utc),
                status="CONFIRMED",
            )
            db.session.add(existing_booking)
            db.session.commit()

        response = self.client.post(
            "/bookings",
            json={
                "parent_id": self.parent_id,
                "lsa_id": self.active_lsa_id,
                "start_time": "2026-08-10T10:30:00+00:00",
                "end_time": "2026-08-10T11:30:00+00:00",
            },
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.get_json()["error"],
            "The selected LSA is already booked for that time range.",
        )

    def test_post_bookings_rejects_invalid_payload(self):
        response = self.client.post(
            "/bookings",
            json={
                "parent_id": self.parent_id,
                "lsa_id": self.active_lsa_id,
                "start_time": "2026-08-10T11:00:00+00:00",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing required field(s): end_time.", response.get_json()["error"])

    def test_post_bookings_returns_404_for_unknown_parent(self):
        response = self.client.post(
            "/bookings",
            json={
                "parent_id": 9999,
                "lsa_id": self.active_lsa_id,
                "start_time": "2026-08-10T10:00:00+00:00",
                "end_time": "2026-08-10T11:00:00+00:00",
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["error"], "Parent not found.")


if __name__ == "__main__":
    unittest.main()
