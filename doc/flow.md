# Overall Flow

This document describes the intended end-to-end backend flow based on the current codebase and the next implementation steps.

## 1. Application Startup

1. `run.py` imports `create_app()` from `app/__init__.py`.
2. `create_app()` creates the Flask app instance.
3. `Config` loads `DATABASE_URL` from environment variables.
4. `db` and `migrate` are initialized.
5. Model imports register metadata for migrations and ORM relationships.

## 2. Database Initialization Flow

1. Alembic migration creates:
   - `parents`
   - `lsa_profiles`
   - `skills`
   - `lsa_skills`
   - `booking_requests`
2. Indexes support lookup by email, activity status, booking status, and booking time ranges.
3. `seed.py` inserts initial records to make local development and testing easier.

## 3. LSA Search Flow

Target behavior for the upcoming API:

1. Client calls `GET /lsas`.
2. Optional query filters are passed, such as skill name.
3. Backend loads only active LSAs by default.
4. Related skills are loaded efficiently with eager loading.
5. Response returns LSA profile data, hourly rate, status, and associated skills.

## 4. Booking Creation Flow

Target behavior for the upcoming API:

1. Client sends `POST /bookings` with:
   - `parent_id`
   - `lsa_id`
   - `start_time`
   - `end_time`
2. Backend validates the payload shape and required fields.
3. Backend verifies that the parent exists.
4. Backend verifies that the LSA exists and is active.
5. Backend checks whether the requested time range overlaps an existing booking for the same LSA.
6. If there is a conflict, backend returns a rejection response such as `409 Conflict`.
7. If the slot is available, backend creates a booking record in a transaction.
8. Backend returns booking details and status.

## 5. Overlap Prevention Logic

Recommended overlap condition for the same `lsa_id`:

```text
existing.start_time < requested.end_time
AND existing.end_time > requested.start_time
```

This catches:
- partial overlaps at the beginning
- partial overlaps at the end
- full containment
- exact-match conflicts

## 6. Data Relationship Flow

- A `Parent` can create many `BookingRequest` records.
- An `LSAProfile` can have many `Skill` records through `LSASkill`.
- An `LSAProfile` can receive many `BookingRequest` records.
- A `BookingRequest` belongs to one parent and one LSA.

## 7. Optional Payment/Webhook Flow

If the assignment requires mock payment handling, the expected flow is:

1. Booking is created in `PENDING` state.
2. Backend simulates or triggers a mock payment request.
3. Payment success changes booking to `CONFIRMED`.
4. Payment failure changes booking to `FAILED`.
5. If webhook handling is part of scope, provider callback updates the booking asynchronously.

If payment is not required, booking can remain a pure reservation workflow.

## 8. Testing Flow

Recommended validation path:

1. Run migrations on a clean database.
2. Seed sample data.
3. Verify model creation.
4. Verify skill mapping.
5. Verify LSA search filtering.
6. Verify successful booking creation.
7. Verify overlap rejection.

## 9. Current Gap Between Code And Target Flow

Already present:
- app factory
- config loading
- models
- migration
- seed script

Still missing:
- routes
- serializers
- service layer
- booking conflict query
- automated tests
- payment integration layer
