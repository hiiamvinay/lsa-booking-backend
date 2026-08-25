# Technical Documentation

## LSA Service Booking Backend

This document contains the detailed technical design and implementation guidance for the LSA Service Booking Backend.

The root `README.md` intentionally focuses on project discovery and setup. This document contains the deeper engineering documentation required to understand, review, test, and extend the backend.

---

## 1. Architecture

### 1.1 Architectural Style

The application follows an MVC-style architecture adapted to a Flask REST API.

```text
HTTP Request
     |
     v
Route / Controller
     |
     v
Service Layer
     |
     +----------------------+
     |                      |
     v                      v
SQLAlchemy Models      External Services
     |                      |
     v                      v
PostgreSQL             Mock Payment API
                            |
                            | Payment Result
                            v
                     Payment Webhook  (/api/payment/webhhook)
                            |
                            v
                     Payment Service
                            |
                            v
                       PostgreSQL
```

### Route / Controller Layer

Responsible for:

- HTTP method and route handling
- Reading query parameters
- Reading JSON request bodies
- Request-level validation
- Calling service functions
- Serializing responses
- HTTP status codes

Routes should remain thin. Business rules should not be duplicated across multiple route functions.

### Service Layer

Responsible for business operations such as:

- Booking validation
- Availability/conflict checks
- Payment initiation
- External payment communication
- Payment result processing

The service layer makes business logic independently testable.

### Model Layer

SQLAlchemy models represent persistent entities:

- `Parent`
- `LSAProfile`
- `Skill`
- `LSASkill`
- `BookingRequest`
- `Payment`

---

## 2. MVC vs MVT

### MVC

MVC means:

- Model
- View
- Controller

A typical REST-oriented interpretation is:

```text
Controller
    |
    +----> Model
    |
    +----> Response / View representation
```

### MVT

Django commonly uses:

- Model
- View
- Template

```text
Request
   |
   v
Django View
   |
   +---- Model
   |
   +---- Template
            |
            v
           HTML
```

MVT is particularly useful for applications where the framework renders HTML templates.

### Why this project uses Flask MVC-style architecture

This application is backend-only and exposes REST APIs. It does not require a server-side HTML template layer.



Therefore, an MVC-style Flask design provides a clear separation:

```text
Route / Controller
        |
        v
Service / Business Logic
        |
        v
SQLAlchemy Model
        |
        v
PostgreSQL
```

This is an architectural convention rather than a claim that Flask imposes one official MVC implementation.

---

# 3. Technology Choices

## 3.1 Flask

Flask is used because the project needs:

- REST endpoints
- Modular routes/Blueprints
- Application-factory support
- SQLAlchemy integration
- Migration integration
- Explicit control over API behavior

## 3.2 PostgreSQL

PostgreSQL is appropriate because the domain is strongly relational.

The application requires:

- Foreign keys
- One-to-many relationships
- Many-to-many relationships
- Transactions
- Constraints
- Indexes
- Reliable concurrent access

## 3.3 SQLAlchemy

SQLAlchemy provides:

- ORM mapping
- Relationship handling
- Query composition
- Eager-loading strategies
- Transaction support

## 3.4 Flask-Migrate / Alembic

Migrations make schema changes reproducible.

Instead of manually executing SQL on every environment, migration files describe changes and can be applied using:

```bash
flask --app run.py db upgrade
```

## 3.5 Requests

Python `requests` is used to demonstrate integration with an external payment service.

The integration explicitly handles:

- Timeouts
- Connection failures
- HTTP errors
- Unexpected request failures

---

# 4. Database Design

```text
┌─────────────────┐
│     parents     │
├─────────────────┤
│ PK id           │
│ name            │
│ email           │
│ phone           │
│ created_at      │
└────────┬────────┘
         │
         │ 1:N
         ▼
┌─────────────────────────┐
│    booking_requests     │
├─────────────────────────┤
│ PK id                   │
│ FK parent_id            │
│ FK lsa_id               │
│ start_time              │
│ end_time                │
│ status                  │
│ amount                  │
│ created_at              │
└───────┬─────────┬───────┘
        │         │
        │ N:1     │ 1:1
        ▼         ▼
┌──────────────┐  ┌─────────────────┐
│ lsa_profiles │  │    payments     │
├──────────────┤  ├─────────────────┤
│ PK id        │  │ PK id           │
│ name         │  │ FK booking_id   │
│ email        │  │ external_id     │
│ hourly_rate  │  │ amount          │
│ is_active    │  │ status          │
│ created_at   │  │ created_at      │
└──────┬───────┘  │ updated_at      │
       │          └─────────────────┘
       │ N:M
       ▼
┌──────────────┐
│  lsa_skills  │
├──────────────┤
│ PK/FK lsa_id │
│ PK/FK skill_id│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    skills    │
├──────────────┤
│ PK id        │
│ name         │
└──────────────┘
```

## 4.1 Entity Relationship

```text
+-----------+
|  Parent   |
+-----------+
     |
     | 1:N
     v
+------------------+
| BookingRequest   |
+------------------+
     |
     | N:1
     v
+-------------+
| LSAProfile  |
+-------------+
     |
     | N:M
     v
+-------------+
|   LSASkill  |
+-------------+
     ^
     |
     | N:M
     |
+-------------+
|    Skill    |
+-------------+

BookingRequest
      |
      | 1:1
      v
+-------------+
|   Payment   |
+-------------+
```

---

## 4.2 Parent

The parent represents the customer making a booking.

Typical fields:

```text
id
name
email
phone
created_at
```

### Relationship

```python
bookings = db.relationship(
    "BookingRequest",
    back_populates="parent",
    lazy="select"
)
```

This means:

```text
Parent
  |
  +--> BookingRequest
  +--> BookingRequest
  +--> BookingRequest
```

One parent can create multiple booking requests.

---

## 4.3 LSAProfile

Represents a Learning Support Assistant.

Typical fields:

```text
id
name
email
hourly_rate
is_active
created_at
```

An inactive LSA remains stored for historical consistency but can be excluded from normal search results.

---

## 4.4 Skill

Represents a capability that an LSA offers.

Example values:

```text
Autism
Dyslexia
ADHD
Reading Support
Mathematics
Speech Support
```

The skill name should be unique.

---

## 4.5 LSASkill

`LSASkill` is the association table for the LSA/Skill many-to-many relationship.

```text
lsa_skills
-----------------
lsa_id
skill_id
```

Without an association table, storing skills as:

```text
"Autism, ADHD, Reading Support"
```

would make filtering, indexing, and referential integrity difficult.

The normalized design allows:

```text
LSA 1 -> Autism
LSA 1 -> ADHD
LSA 1 -> Reading Support

LSA 2 -> Autism
```
Sample Table to understand the relationship

```txt

lsa_profiles                 skills
┌────┬─────────────┐         ┌────┬─────────────────┐
│ id │ name        │         │ id │ name            │
├────┼─────────────┤         ├────┼─────────────────┤
│ 1  │ Amit Kumar  │         │ 1  │ Autism          │
│ 2  │ Neha Singh  │         │ 2  │ Dyslexia        │
│ 3  │ Ravi Mehta  │         │ 3  │ ADHD            │
│ 4  │ Sneha Patel │         │ 4  │ Reading Support │
└────┴─────────────┘         │ 5  │ Mathematics     │
                             │ 6  │ Speech Support  │
                             └────┴─────────────────┘
                  │
                  │
                  ▼
             lsa_skills
          ┌─────────┬──────────┐
          │ lsa_id  │ skill_id │
          ├─────────┼──────────┤
          │    1    │    1     │
          │    1    │    4     │
          │    2    │    2     │
          │    2    │    5     │
          │    3    │    1     │
          │    3    │    3     │
          │    3    │    4     │
          │    4    │    6     │
          │    4    │    1     │
          └─────────┴──────────┘

```

---

## 4.6 BookingRequest

Represents a requested session.

Typical fields:

```text
id
parent_id
lsa_id
start_time
end_time
status
created_at
updated_at
```

Foreign keys:

```text
parent_id -> parents.id
lsa_id    -> lsa_profiles.id
```

Typical state machine:

```text
PENDING
   |
   +----> CONFIRMED
   |
   +----> PAYMENT_FAILED
   |
   +----> CANCELLED
```

The actual implementation should define and enforce only the states supported by the application.

---

## 4.7 Payment

Payment is modeled separately from booking.

Typical fields:

```text
id
booking_id
external_payment_id
amount
status
created_at
updated_at
```

Payment state:

```text
PENDING
   |
   +----> SUCCESS
   |
   +----> FAILED
```

### Why separate Payment from Booking?

A booking and payment are related but represent different business concepts.

The booking answers:

> "Is this session reserved/confirmed?"

The payment answers:

> "What is the payment state for this booking?"

The payment also needs its own external provider identifier.

Separating them avoids coupling the booking table to provider-specific payment details.

---

# 5. API Specification

The API is JSON-based.

## 5.1 LSA Search

### Endpoint

```http
GET /api/lsas/search/
```

### Query parameters

```text
skill
skill_id
page
per_page
```

Example:

```http
GET /api/lsas/search/?skill=ADHD
```

### Behavior

The endpoint should:

1. Start with the LSA query.
2. Exclude inactive LSAs by default, if required by the API contract.
3. Filter by skill when provided.
4. Eager-load related skills.
5. Apply pagination.
6. Return JSON.

### Example response

```json
{
  "count": 1,
  "data": [
    {
      "created_at": "2026-08-10T22:22:25.265491+05:30",
      "email": "ravi.lsa@example.com",
      "hourly_rate": 750.0,
      "id": 3,
      "is_active": true,
      "name": "Ravi Mehta",
      "skills": [
        {
          "id": 3,
          "name": "ADHD"
        },
        {
          "id": 1,
          "name": "Autism"
        },
        {
          "id": 4,
          "name": "Reading Support"
        }
      ]
    }
  ],
  "page": 1,
  "per_page": 10
}

```

### Errors

```text
400 -> Invalid pagination/filter parameters
500 -> Unexpected server failure
```

---

## 5.2 Create Booking

### Endpoint

```http
POST /api/bookings/
```

### Request

```json
{
  "parent_id": 2,
  "lsa_id": 2,
  "start_time": "2026-08-12T08:00:00+00:00",
  "end_time": "2026-08-12T09:00:00+00:00"
}
```

### Validation sequence

```text
Request Body
    │
    ▼
Required Fields
    │
    ▼
Datetime Parsing
    │
    ▼
start_time < end_time
    │
    ▼
Parent Exists
    │
    ▼
LSA Exists
    │
    ▼
LSA is Bookable
    │
    ▼
Overlap Check
    │
    ▼
Create Booking
    │
    ▼
Booking = PENDING
    │
    ▼
Create Payment
    │
    ▼
Call Mock Payment Service
    │
    ▼
Payment Webhook (api/payment/webhook)
    │
    ▼
Payment Service
    │
    ├───────────────┐
    ▼               ▼
COMPLETED         FAILED
    │               │
    ▼               ▼
Booking           Booking
COMPLETED         FAILED
```
### Success

```http
201 Created
```

Example:

```json
{
  "data": {
    "booking_id": 14,
    "booking_status": "COMPLETED",
    "payment": {
      "amount": 900.0,
      "external_payment_id": "pay_6436c8ef6273",
      "payment_id": 14,
      "payment_status": "COMPLETED"
    }
  }
}
```

### Errors

```text
400 INVALID_REQUEST
404 PARENT_NOT_FOUND
404 LSA_NOT_FOUND
409 BOOKING_CONFLICT
500 INTERNAL_ERROR
502 EXTERNAL PAYMENT SERVICE ERROR
```

Example:

```json
{
  "error": {
    "code": "BOOKING_CONFLICT",
    "message": "LSA is already booked for the requested time."
  }
}
```

---

## 5.3 Payment Webhook

### Endpoint

```http
POST /api/payments/webhook/
```

### Example payload

```json
{
  "payment_id": "pay_12345",
  "booking_id": 101,
  "status": "success"
}
```

### Success handling

```text
Payment PENDING
       |
       v
Payment SUCCESS

Booking PENDING
       |
       v
Booking CONFIRMED
```

### Failure handling

```text
Payment PENDING
       |
       v
Payment FAILED

Booking PENDING
       |
       v
Booking PAYMENT_FAILED
```

### Duplicate events

A webhook provider may retry delivery.

The webhook handler therefore needs idempotent behavior. Receiving the same successful event twice must not create another payment or cause an invalid state transition.

---

# 6. Query Optimization

## 6.1 N+1 Problem

Suppose 100 LSAs are returned.

A naive implementation may execute:

```text
1 query -> retrieve 100 LSAs

100 additional queries
-> retrieve skills for each LSA
```

Total:

```text
101 queries
```

This is the N+1 query problem.

---

## 6.2 Bad Query Pattern

```python
lsas = LSAProfile.query.all()

for lsa in lsas:
    print(lsa.skills)
```

If `skills` is lazily loaded, each access can trigger another query.

---

## 6.3 Optimized Query

Use SQLAlchemy eager loading:

```python
from sqlalchemy.orm import selectinload

query = LSAProfile.query.options(
    selectinload(LSAProfile.skills)
)
```
which is equivalent to 

```sql
SELECT
    lsa_skills.lsa_id,
    skills.id,
    skills.name
FROM skills
JOIN lsa_skills
    ON skills.id = lsa_skills.skill_id
WHERE lsa_skills.lsa_id IN (
    SELECT id
    FROM lsa_profiles
);

```

Conceptually:

```text
Query 1:
    Load LSAs

Query 2:
    Load skills for those LSAs
```

Instead of:

```text
Query 1:
    Load LSAs

Query 2..N:
    Load skills individually
```

### Why `selectinload`?

`selectinload` is well suited to collection relationships. SQLAlchemy can retrieve related records for the selected parent IDs in a separate query.

This avoids one query per parent row while also avoiding unnecessarily large joined result sets.

---

## 6.4 Filtering

Filtering should happen in the database rather than loading all records into Python.

Prefer:

```python
query = query.filter(LSAProfile.is_active.is_(True))
```

rather than:

```python
lsas = [
    lsa for lsa in LSAProfile.query.all()
    if lsa.is_active
]
```

The first approach allows PostgreSQL to perform the filtering.

---



## 6.4 Indexes

Indexes should correspond to real query patterns.

Potential indexes:

```text
lsa_profiles.is_active
lsa_skills.lsa_id
lsa_skills.skill_id
booking_requests.lsa_id
booking_requests.start_time
booking_requests.end_time
payments.booking_id
payments.external_payment_id
```
```text
skill.name
```

### Booking conflict queries

The booking availability query commonly filters by:

```text
lsa_id
start_time
end_time
status
```

An appropriate indexing strategy should be selected after considering the actual query and PostgreSQL query plan.

Indexes are not free. They consume storage and make writes more expensive, so the project avoids adding indexes without a query-driven reason.

---

# 7. Booking and Double-Booking Prevention

## 7.1 What is a double booking?

A double booking occurs when two booking requests reserve the same LSA for overlapping sessions.

### Invalid

```text
Existing:
LSA 1 | 10:00 -------- 11:00

New:
LSA 1 | 10:30 -------- 11:30
```

### Valid

```text
Existing:
LSA 1 | 10:00 -------- 11:00

New:
LSA 1 | 11:00 -------- 12:00
```

assuming adjacent sessions are allowed by the business rule.

### Also valid

```text
Parent A -> LSA 1 -> 10:00-11:00
Parent B -> LSA 2 -> 10:00-11:00
```

The conflict is scoped to the same LSA.

---

## 7.2 Overlap condition

For half-open time intervals:

```text
new_start < existing_end
AND
new_end > existing_start
```

If both conditions are true, the intervals overlap.

---


## 7.3 Concurrency consideration

A simple application-level "check then insert" can still have a race condition if two requests execute simultaneously:

```text
Request A -> checks availability -> free
Request B -> checks availability -> free
Request A -> inserts
Request B -> inserts
```

A production-grade implementation should therefore consider database-level concurrency protection appropriate to the PostgreSQL schema and transaction isolation strategy.

Possible approaches include:

- Appropriate transaction isolation/locking.
- PostgreSQL exclusion constraints for time ranges.
- Advisory locks where appropriate.
- A carefully designed serializable transaction.

For a small assessment prototype, the application-level conflict check demonstrates the business rule; the final production choice should be documented based on expected concurrency.

---

# 8. Payment Integration

## 8.1 Why a Payment Entity?

A booking and payment have separate lifecycles.

```text
Booking:
PENDING -> CONFIRMED / PAYMENT_FAILED

Payment:
PENDING -> SUCCESS / FAILED
```

The payment also needs:

```text
external_payment_id
amount
status
timestamps
```

Therefore payment is represented by its own model.

---

## 8.2 Outbound Payment Request

The backend calls the mock external service:

```text
Flask Backend
     |
     | POST /payments
     | requests.post(...)
     v
Mock Payment Service
```

Example:

```python
response = requests.post(
    payment_service_url,
    json={
        "booking_id": booking.id,
        "amount": payment.amount
    },
    timeout=5
)

response.raise_for_status()
```

---

## 8.3 Failure Handling

External services can fail.

The integration should handle:

```python
requests.Timeout
requests.ConnectionError
requests.HTTPError
requests.RequestException
```

The API should return a controlled error rather than exposing an internal traceback.

Logging should contain enough information to diagnose the failure without exposing secrets.

---

# 9. Webhook Architecture

The payment workflow has two distinct directions.

### Outbound

```text
Main API
   |
   | requests.post()
   v
Payment Service
```

### Inbound

```text
Payment Service
   |
   | POST webhook
   v
Main API
```


## 9.1 State transitions

### Success

```text
Payment:
PENDING
   |
   v
SUCCESS

Booking:
PENDING
   |
   v
CONFIRMED
```

### Failure

```text
Payment:
PENDING
   |
   v
FAILED

Booking:
PENDING
   |
   v
PAYMENT_FAILED
```

---

## 9.2 Webhook idempotency

Webhook providers commonly retry events when they do not receive a successful acknowledgement.

The handler should therefore tolerate duplicate events.

A safe approach is to use the provider's unique payment/event identifier and enforce appropriate uniqueness in the database.

Repeated processing should not:

- Create a second payment.
- Create a second booking.
- Move a booking into an invalid state.
- Double-apply a financial operation.

---

# 10. Error Handling and Logging

## 10.1 API errors

Use consistent JSON errors:

```json
{
  "error": {
    "code": "BOOKING_CONFLICT",
    "message": "LSA is already booked for the requested time."
  }
}
```

Recommended status codes:

| Status | Use |
|---|---|
| 200 | Successful retrieval/update |
| 201 | Resource creation |
| 400 | Invalid input |
| 404 | Resource does not exist |
| 409 | Business conflict |
| 500 | Unexpected internal failure |
| 502 | External dependency failure |

---

## 10.2 External HTTP timeouts

Never allow an external request to wait indefinitely.

Use:

```python
requests.post(
    url,
    json=payload,
    timeout=5
)
```

The exact timeout should be chosen based on the service's expected behavior.

---

## 10.3 Logging

Log meaningful operational events:

```text
INFO:
Payment request started
Payment request succeeded
Webhook received
Booking state transitioned

WARNING:
Payment service returned an unexpected response

ERROR:
Payment service timeout
Payment service connection failure
Database transaction failure
```

Use exception tracebacks for unexpected failures when useful.

Never log:

```text
Passwords
API secrets
Authorization tokens
Card numbers
CVV
Webhook secrets
```

---

# 11. Database Migrations

## 11.1 Initialize

Only for a project that does not already have a migration environment:

```bash
flask --app run.py db init
```

## 11.2 Generate

After changing models:

```bash
flask --app run.py db migrate -m "add payment model"
```

The generated migration must be reviewed.

## 11.3 Apply

```bash
flask --app run.py db upgrade
```

## 11.4 Clone workflow

A developer cloning the repository should:

```bash
git clone <repository-url>
cd lsa-booking-backend

flask --app run.py db upgrade
```

They should not run:

```bash
flask db init
```

because the migration environment already exists in the repository.

---

# 12. Seed Data

`seed.py` provides representative development data.

Typical records include:

### Parents

```text
Rahul Sharma
Priya Verma
Amit Patel
```

### Skills

```text
Autism
Dyslexia
ADHD
Reading Support
Mathematics
Speech Support
```

### LSAs

The seed data can contain both active and inactive LSAs so that filtering behavior can be tested.

Run:

```bash
python seed.py
```

The script should be safe against accidental duplicate execution according to its implementation.

Seed data is not production data.

---

# 13. Testing Strategy

Testing is organized around business behavior.

## 13.1 LSA search tests

Test:

- Skill filtering.
- Active/inactive behavior.
- Pagination.
- Empty results.
- Related skill serialization.
- Invalid query parameters.

## 13.2 Booking tests

Test:

- Valid booking.
- Missing fields.
- Invalid parent.
- Invalid LSA.
- Invalid time range.
- Overlapping booking.
- Adjacent non-overlapping booking.
- Different LSAs at the same time.

## 13.3 Payment tests

Test:

- Successful external request.
- Timeout.
- Connection error.
- HTTP error.
- Unexpected external response.

External requests should generally be mocked in unit tests so tests are deterministic.

## 13.4 Webhook tests

Test:

- Successful payment.
- Failed payment.
- Invalid payload.
- Unknown payment.
- Duplicate webhook.
- Correct booking state transition.

---

# 14. GitHub Actions / CI

## 14.1 Why PostgreSQL is part of CI

The application depends on PostgreSQL behavior, so database-backed tests should execute against PostgreSQL rather than an unrelated database.

GitHub Actions can start PostgreSQL as a temporary service container.

```text
GitHub Actions Runner
       |
       +-- Python 3.12
       |
       +-- PostgreSQL 16
       |
       +-- Tests
```

## 14.2 Workflow

```text
Push / Pull Request
        |
        v
Checkout
        |
        v
Setup Python
        |
        v
Start PostgreSQL
        |
        v
Install requirements
        |
        v
flask db upgrade
        |
        v
pytest
        |
        v
PASS / FAIL
```

## 14.3 Workflow example

```yaml
name: Run Tests

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: lsa_booking_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
        options: >-
          --health-cmd "pg_isready -U postgres -d lsa_booking_test"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    env:
      FLASK_APP: run.py
      DATABASE_URL: postgresql://postgres:postgres@localhost:5432/lsa_booking_test
      TEST_DATABASE_URL: postgresql://postgres:postgres@localhost:5432/lsa_booking_test
      PAYMENT_SERVICE_URL: http://localhost:5001
      PAYMENT_WEBHOOK_URL: http://localhost:5000/api/payments/webhook/

    steps:
      - name: Check out code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run migrations
        run: flask db upgrade

      - name: Run tests
        run: pytest -q tests
```

If payment integration tests require the mock payment server to be running as a separate process, the CI workflow must also start that service before those tests.

---

# 15. Git Branching Strategy

The repository uses short-lived feature branches.

## Branch names

```text
feature/<description>
fix/<description>
test/<description>
docs/<description>
refactor/<description>
ci/<description>
```

Examples:

```text
feature/lsa-search
feature/booking-api
feature/payment-webhook
fix/booking-overlap
test/payment-webhook
docs/api-documentation
ci/github-actions
```

`main` represents stable code.

---

# 16. Pull Request Workflow

## Step 1

Update local main:

```bash
git checkout main
git pull origin main
```

## Step 2

Create a feature branch:

```bash
git checkout -b feature/booking-api
```

## Step 3

Implement and test:

```bash
pytest -q
```

## Step 4

Commit a focused change:

```bash
git add .
git commit -m "feat: add booking API"
```

## Step 5

Push:

```bash
git push -u origin feature/booking-api
```

## Step 6

Open a Pull Request against `main`.

The PR should contain:

```text
Summary
Implementation details
Database/migration changes
Tests
Known limitations
```

## Example PR

```markdown
## Summary

- Added POST /api/bookings/
- Added request validation.
- Added overlap detection.
- Added 409 conflict response.

## Database

No schema change.

## Testing

pytest -q

All booking tests pass.
```

## CI requirement

GitHub Actions should pass before merging.

---

# 17. Commit Convention

Use focused commits:

```text
feat: add LSA search endpoint
feat: add booking API
feat: add payment webhook
fix: prevent overlapping bookings
test: add booking conflict tests
refactor: move payment logic to service layer
docs: update API documentation
ci: add PostgreSQL test service
```

Avoid vague commits:

```text
update
changes
final
final2
working
```

Focused commits make code review and debugging easier.

---

# 18. Environment and Secrets

Local environment:

```env
DATABASE_URL=postgresql://lsa_user:your_password@localhost:5432/lsa_booking
PAYMENT_SERVICE_URL=http://localhost:5001
PAYMENT_WEBHOOK_URL=http://localhost:5000/api/payments/webhook/
PAYMENT_WEBHOOK_SECRET=change-me
```

Commit only:

```text
.env.example
```

Do not commit:

```text
.env
```

Never expose credentials in source code, logs, or documentation.

---

# 19. Local Development Workflow

Recommended sequence:

```text
1. Pull latest main
       |
2. Create feature branch
       |
3. Modify model if necessary
       |
4. Generate migration
       |
5. Review migration
       |
6. Apply migration
       |
7. Implement route/service
       |
8. Add tests
       |
9. Run tests
       |
10. Commit
       |
11. Push
       |
12. Open PR
       |
13. CI validates
       |
14. Merge
```

---

# 20. Design Decisions

## Why PostgreSQL?

The domain is relational and requires foreign keys, transactions, joins, indexes, and concurrency-aware booking behavior.

## Why SQLAlchemy?

It provides ORM relationships, query composition, eager loading, and transaction support while remaining explicit enough for performance-sensitive backend code.

## Why a separate service layer?

It keeps business rules out of HTTP route functions and makes the core operations easier to test.

## Why a separate Payment model?

Payment has an independent lifecycle and external provider identity.

## Why a webhook?

Payment completion may happen asynchronously. The webhook communicates the provider's final state to the backend.

## Why a mock payment service?

The assignment requires third-party integration behavior without requiring a real payment provider.

## Why eager loading?

LSA search needs skills. Eager loading prevents the N+1 pattern and reduces database round trips.

## Why migrations?

Migrations make the schema reproducible across development, testing, CI, and deployment environments.

## Why feature branches?

They keep changes isolated and make Pull Requests easier to review.

---

# 21. Production Considerations and Future Improvements

The assessment prototype can be extended with:

- Authentication and authorization.
- Role-based permissions.
- Webhook signature verification.
- Strong idempotency keys.
- Database-level PostgreSQL exclusion constraints for time-range conflicts.
- Redis caching.
- Rate limiting.
- Celery/background jobs.
- Real payment provider integration.
- OpenAPI/Swagger.
- Structured JSON logging.
- Metrics and health checks.
- Distributed tracing.
- Docker Compose.
- Containerized deployment.
- Automated deployment.
- Load and concurrency testing.

For high-concurrency production booking systems, the overlap rule should be enforced with an appropriate database-level strategy rather than relying only on an application-level pre-check.

---

