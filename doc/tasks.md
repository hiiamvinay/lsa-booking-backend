# Tasks To Complete

This document lists the remaining work needed to take the repository from data-model foundation to a complete backend assignment submission.

## Priority 1: API Foundation

- Create route modules for LSA search and booking creation
- Register blueprints inside `create_app()`
- Add request parsing and response serialization
- Standardize JSON success and error responses

## Priority 2: Business Logic

- Implement service logic for creating booking requests
- Validate `parent_id`, `lsa_id`, `start_time`, and `end_time`
- Prevent invalid ranges where `end_time <= start_time`
- Reject bookings for inactive LSAs
- Add overlap detection for existing bookings on the same LSA
- Decide which booking statuses block new reservations, such as `PENDING` and `CONFIRMED`

## Priority 3: Search Flow

- Add `GET /lsas` endpoint
- Support filtering by skill name or skill id
- Return only active LSAs by default
- Include related skills in the response
- Avoid N+1 queries using eager loading

## Priority 4: Booking Lifecycle

- Define booking statuses clearly, for example `PENDING`, `CONFIRMED`, `CANCELLED`, and `FAILED`
- Decide whether booking creation immediately confirms the booking or creates a pending state
- Add a booking detail endpoint to inspect final state
- Add cancellation or expiration behavior if required

## Priority 5: Payment and Webhook Scope

- Confirm whether the assignment requires only mock external integration or a separate payment entity
- If payment support is required, add:
- payment status tracking
- mock provider call abstraction
- webhook handler endpoint
- booking status updates driven by payment success or failure

## Priority 6: Validation and Error Handling

- Add central error response helpers
- Return `400` for invalid payloads
- Return `404` for missing parent or LSA records
- Return `409` for booking conflicts
- Return `422` for domain validation failures if used by the team convention

## Priority 7: Test Coverage

- Add pytest to project dependencies
- Create app and database fixtures
- Add model tests
- Add booking conflict tests
- Add search filter tests
- Add API integration tests for success and failure scenarios

## Priority 8: Delivery Readiness

- Add `.env.example`
- Add README API examples after routes exist
- Add CI workflow for linting and tests
- Add logging around booking creation and conflict rejection
- Review timezone handling end to end

## Suggested Build Order

1. Add blueprints and route registration.
2. Implement booking service logic with overlap checks.
3. Implement LSA search endpoint with eager loading.
4. Add consistent serializers and error responses.
5. Add tests around the happy path and conflict cases.
6. Extend into payment or webhook behavior only if the assignment requires it.

## Definition Of Done

The backend should be considered complete when:
- migrations run cleanly on a fresh database
- seed data loads successfully
- LSA search works with skill-based filtering
- booking creation rejects invalid or overlapping requests
- tests cover the core business flow
- documentation matches the actual codebase
