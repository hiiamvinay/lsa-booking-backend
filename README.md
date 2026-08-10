# LSA Booking Backend

Backend service for managing Learning Support Assistant (LSA) discovery and booking. The project is built with Flask, SQLAlchemy, and Alembic, and currently includes the core data model, database migration, and seed data needed to start implementing the API layer.

## Current Status

This repository is in the foundation stage.

Implemented today:
- Flask application factory setup
- SQLAlchemy and Flask-Migrate integration
- Core models for `Parent`, `LSAProfile`, `Skill`, `LSASkill`, and `BookingRequest`
- Initial Alembic migration
- Seed script for sample parents, LSAs, and skills

Planned next:
- REST API endpoints for booking and LSA search
- Business logic for overlap prevention
- Validation and error handling
- Tests
- Mock payment integration and webhook flow if required by the assignment

## Problem Statement

Parents need a reliable way to find LSAs with the right skills and request time-bound bookings without creating conflicting schedules. This backend is intended to support:
- LSA profile discovery
- Skill-based filtering
- Booking request creation
- Double-booking prevention
- Clean persistence and migration workflow

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Alembic
- PostgreSQL via `psycopg2-binary`
- `python-dotenv` for environment loading

## Project Structure

```text
lsa-booking-backend/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   └── models/
│       ├── booking.py
│       ├── lsa.py
│       ├── parent.py
│       └── skill.py
├── doc/
│   ├── flow.md
│   └── tasks.md
├── migrations/
├── tests/
├── requirements.txt
├── run.py
└── seed.py
```

## Data Model

### Parent
- Stores parent identity and contact information
- Has many booking requests

### LSAProfile
- Stores LSA identity, activity status, and hourly rate
- Has many skills through the `lsa_skills` join table
- Has many booking requests

### Skill
- Reusable skill catalog such as `Autism`, `ADHD`, and `Reading Support`

### BookingRequest
- Connects a parent to an LSA for a requested time range
- Tracks booking status
- Includes a composite index on `lsa_id`, `start_time`, and `end_time` to support booking conflict checks

## Current Database Flow

1. App bootstraps through `create_app()`.
2. Config loads `DATABASE_URL` from `.env`.
3. SQLAlchemy initializes tables through Alembic migrations.
4. `seed.py` inserts sample skills, parents, and LSAs.
5. Future API routes will query these models for search and booking operations.

More implementation detail is documented in [doc/flow.md](/home/vinay/project/lsa-booking-backend/doc/flow.md) and [doc/tasks.md](/home/vinay/project/lsa-booking-backend/doc/tasks.md).

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file with:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/lsa_booking
```

### 4. Run migrations

```bash
flask db upgrade
```

If the Flask app entry point is needed in your shell:

```bash
export FLASK_APP=run.py
```

### 5. Seed the database

```bash
python seed.py
```

### 6. Run the development server

```bash
python run.py
```

## Seed Data

The seed script currently inserts:
- 3 parents
- 4 LSA profiles
- 6 skills
- Skill-to-LSA assignments

It skips execution if parent data already exists, which prevents duplicate seed runs in a non-empty database.

## API Direction

The intended API surface for the next implementation stage is:
- `GET /lsas` for list and skill-based filtering
- `POST /bookings` for new booking requests
- `GET /bookings/<id>` for booking details
- Optional payment endpoints or webhook handlers depending on assignment scope

## Concurrency and Booking Safety

The booking model already supports the foundation for overlap checks, but conflict prevention still needs to be implemented in the service layer. The expected logic is:
- validate the requested time range
- check if the selected LSA is active
- query overlapping bookings for the same LSA
- reject conflicts before insert
- wrap create operations in a transaction

## Testing

The `tests/` directory exists but does not yet contain automated coverage. Recommended first tests:
- create valid parent and LSA records
- attach skills to LSAs
- create a valid booking request
- reject booking overlaps
- filter LSAs by skill and activity status

## Notes

- The repository currently contains models and migration scaffolding, but not route, schema, or service modules yet.
- The original lightweight `doc.md` has been replaced with a `doc/` folder so planning and system flow can live in separate documents.

## Next References

- Task breakdown: [doc/tasks.md](/home/vinay/project/lsa-booking-backend/doc/tasks.md)
- Request and booking lifecycle: [doc/flow.md](/home/vinay/project/lsa-booking-backend/doc/flow.md)
