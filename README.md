# LSA Service Booking Backend

Production-style REST API for managing Learning Support Assistant (LSA) discovery, booking, and payment workflows.

The project is built as a Flask backend with PostgreSQL and SQLAlchemy. It demonstrates relational data modeling, REST API design, booking conflict prevention, third-party payment integration, webhook-driven state transitions, automated testing, logging, migrations, and GitHub Actions CI.

> **Frontend:** This repository is backend-only. No frontend application is included.

---

## Quick Navigation

- [Features](#features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Database Setup](#database-setup)
- [Migrations](#migrations)
- [Seed Data](#seed-data)
- [Run the API](#run-the-api)
- [Run Tests](#run-tests)
- [CI](#ci)
- [API Overview](#api-overview)
- [Technical Documentation](#technical-documentation)
- [Git Workflow](#git-workflow)
- [Security](#security)

---

## Features

- LSA profile management and skill relationships
- Skill-based LSA search
- Pagination
- SQLAlchemy ORM
- PostgreSQL relational database
- Flask-Migrate / Alembic database migrations
- Booking creation and validation
- Overlapping-session detection
- Double-booking prevention for the same LSA
- Separate payment entity and payment lifecycle
- Mock third-party payment service
- `requests`-based external API integration
- External API timeout and exception handling
- Payment webhook processing
- Booking state transitions based on payment results
- Application logging
- Pytest test suite
- PostgreSQL-backed GitHub Actions CI
- Structured Git branching and pull-request workflow

---

## Architecture

The application follows an MVC-style architecture adapted for a Flask REST API.

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
                     Payment Webhook
                            |
                            v
                     Payment Service
                            |
                            v
                       PostgreSQL
```

The API does not render server-side HTML. It returns JSON responses, so the application uses a controller/service/model separation rather than a template-oriented architecture.

For the detailed MVC vs MVT discussion, database design, booking concurrency approach, payment flow, and query optimization, see:

**[`docs/TECHNICAL_DOCUMENTATION.md`](docs/TECHNICAL_DOCUMENTATION.md)**

---

## Technology Stack

| Category | Technology |
|---|---|
| Language | Python 3.12 |
| Web framework | Flask |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Migrations | Flask-Migrate / Alembic |
| HTTP client | Requests |
| Testing | Pytest |
| CI | GitHub Actions |
| Version control | Git / GitHub |
| Optional local containerization | Docker |

---

## Project Structure

```text
lsa-booking-backend/
│
├── app/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── config.py
│   ├── extensions.py
│   └── __init__.py
│
├── mock_payment/
│   └── app.py
│
├── tests/
│
├── migrations/
│   └── versions/
│
├── docs/
│   └── TECHNICAL_DOCUMENTATION.md
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── seed.py
├── run.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

# Quick Start

## Prerequisites

Install:

- Python 3.12
- PostgreSQL
- Git
- pip

Verify:

```bash
python3 --version
psql --version
git --version
```

## 1. Clone the repository

```bash
git clone <repository-url>
cd lsa-booking-backend
```

## 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Configure environment variables

Copy the example file:

```bash
cp .env.example .env
```

Edit `.env` with your local PostgreSQL credentials and service URLs.

Example:

```env
DATABASE_URL=postgresql://lsa_user:your_password@localhost:5432/lsa_booking
TEST_DATABASE_URL=postgresql://lsa_user:your_password@localhost:5432/lsa_booking
PAYMENT_SERVICE_URL=http://localhost:5001
PAYMENT_WEBHOOK_URL=http://localhost:5000/api/payments/webhook/
```

## 5. Create the database

Open PostgreSQL:

```bash
sudo -u postgres psql
```

Create the application user:

```sql
CREATE USER lsa_user WITH PASSWORD 'your_password';
```

Create the database:

```sql
CREATE DATABASE lsa_booking OWNER lsa_user;
CREATE DATABASE lsa_booking_test OWNER lsa_user;

```

Exit:

```sql
\q
```

## 6. Apply migrations

Do not recreate the migration environment after cloning the repository.

Run:

```bash
flask --app run.py db upgrade
```

## 7. Load development data

```bash
python seed.py
```

## 8. Start the API

```bash
python run.py
```

The default development API is expected at:

```text
http://localhost:5000
```

## 9. Start the mock payment service

In another terminal:

```bash
source venv/bin/activate
python mock_payment/app.py
```

The mock service is expected at:

```text
http://localhost:5001
```

---

# Database Setup

The application uses PostgreSQL as its relational database.

The main entities are:

```text
Parent
   |
   +----< BookingRequest >---- LSAProfile
                                  |
                                  +----< LSASkill >---- Skill

BookingRequest
   |
   +---- Payment
```

The detailed schema, relationship rationale, constraints, and indexing strategy are documented in:

**[`docs/TECHNICAL_DOCUMENTATION.md`](docs/TECHNICAL_DOCUMENTATION.md)**

---

# Migrations

Migration files are version-controlled under:

```text
migrations/versions/
```

### Generate a migration after changing models

```bash
flask --app run.py db migrate -m "describe schema change"
```

Review the generated migration before applying it.

### Apply migrations

```bash
flask --app run.py db upgrade
```

### View migration history

```bash
flask --app run.py db history
```

### Check current revision

```bash
flask --app run.py db current
```

> **Important:** `flask db migrate` creates a migration from model changes. `flask db upgrade` applies existing migrations. A developer cloning this repository normally needs `db upgrade`, not `db init`.

---

# Seed Data

Development/sample records can be inserted using:

```bash
python seed.py
```

The seed script creates representative:

- Parents
- LSA profiles
- Skills
- LSA-skill associations

Seed data is intended for development and testing only.

---

# Run the API

Start the main Flask application:

```bash
python run.py
```

Expected development address:

```text
http://localhost:5000
```

---

# Run Tests

## 4. Run the test cases

After the test database has been migrated:

```bash
pytest -q tests
```

For verbose output:

```bash
pytest -v tests
```



## Complete local testing workflow

For a fresh test database, the complete sequence is:

```bash
export FLASK_CONFIG=testing

flask db upgrade

pytest -q tests
```

### Important

The test suite should use `lsa_booking_test`, not the development database.

```text
                 Flask
                   |
          FLASK_CONFIG=testing
                   |
                   v
          lsa_booking_test
                   |
          +--------+--------+
          |                 |
     flask db upgrade     pytest
          |                 |
          v                 v
      Test schema       Test cases
```

Do not run the development seed script against the test database unless a particular test explicitly requires that data. Tests should normally create their own test data/fixtures.

# CI

The repository uses GitHub Actions to validate changes automatically.

The CI workflow:

```text
Push / Pull Request
        |
        v
Checkout repository
        |
        v
Set up Python 3.12
        |
        v
Start PostgreSQL 16
        |
        v
Install dependencies
        |
        v
Run database migrations
        |
        v
Run Pytest
        |
        v
PASS / FAIL
```

The CI PostgreSQL instance is temporary and isolated from the developer's local database.

Workflow file:

```text
.github/workflows/test.yml
```

---

# API Overview

The primary backend capabilities are:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/lsas/search/` | Search LSAs by skill with pagination |
| `POST` | `/api/bookings/` | Create a booking request |
| `POST` | `/api/payments/webhook/` | Receive payment result events |

The exact request/response contracts, validation rules, status codes, and examples are documented in:

**[`docs/TECHNICAL_DOCUMENTATION.md`](docs/TECHNICAL_DOCUMENTATION.md)**

---

# Booking and Payment Flow

A booking starts in a pending state.

```text
Create Booking
      |
      v
Booking = PENDING
      |
      v
Payment = PENDING
      |
      v
Mock Payment Service
      |
      v
Webhook  (Payment Service)
      |
  +---+---+
  |       |
SUCCESS  FAILED
  |       |
  v       v
CONFIRMED  PAYMENT_FAILED
```

The application rejects overlapping sessions for the same LSA.

Different LSAs can be booked at the same time.

The detailed overlap rule, transaction behavior, payment integration, webhook lifecycle, and idempotency considerations are documented in the technical documentation.

---

# Technical Documentation

The repository separates quick-start documentation from detailed engineering documentation.

## Detailed technical documentation

**[`docs/TECHNICAL_DOCUMENTATION.md`](docs/TECHNICAL_DOCUMENTATION.md)**

It covers:

- Architecture
- MVC vs MVT
- Flask architectural rationale
- Database entities and relationships
- API specifications
- Request/response examples
- Validation rules
- N+1 query problem
- `selectinload` optimization
- Indexing strategy
- Double-booking prevention
- Transaction boundaries
- Payment integration
- Webhook architecture
- Payment and booking state transitions
- Exception handling
- Logging
- Database migrations
- Testing strategy
- GitHub Actions
- Git branching
- Pull-request workflow
- Design decisions
- Future production improvements

---

# Git Workflow

The repository uses short-lived feature branches.

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

Typical workflow:

```bash
git checkout main
git pull origin main

git checkout -b feature/booking-api

git add .
git commit -m "feat: add booking API"

git push -u origin feature/booking-api
```

Open a Pull Request against `main`.

GitHub Actions should pass before merging.

Detailed branching and PR conventions are documented in:

**[`docs/TECHNICAL_DOCUMENTATION.md`](docs/TECHNICAL_DOCUMENTATION.md)**

---

# Environment and Secrets

Never commit `.env` or real secrets.

Use:

```text
.env.example
```

for documenting required configuration.

`.gitignore` should include:

```gitignore
.env
venv/
__pycache__/
*.pyc
.pytest_cache/
.coverage
.idea/
.vscode/
```

Never log or commit:

- Passwords
- API keys
- Access tokens
- Payment secrets
- Card information
- CVV

---

# Design Principles

The project follows these principles:

- Keep HTTP concerns inside routes/controllers.
- Keep business rules in services.
- Keep persistence concerns in SQLAlchemy models.
- Keep schema changes in version-controlled migrations.
- Validate input before persistence.
- Use transactions for related state changes.
- Prevent N+1 database access.
- Use timeouts for external HTTP calls.
- Handle external-service failures explicitly.
- Treat webhook events as asynchronous state changes.
- Keep payment state separate from booking state.
- Test both successful and failure paths.
- Automate testing through CI.
- Keep commits focused and pull requests reviewable.

---

# Further Reading

For complete implementation details, see:

**[`docs/TECHNICAL_DOCUMENTATION.md`](docs/TECHNICAL_DOCUMENTATION.md)**
