# Vital Path — Backend

FastAPI backend for Vital Path, a patient navigation platform that helps users find accessible healthcare facilities, book appointments, and track required documents.

## Tech Stack

- **FastAPI** + **Pydantic**
- **SQLAlchemy** ORM
- **SQLite** locally, **PostgreSQL (Neon)** in production
- Deployed on **Render**

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file (gitignored):

```
# leave DATABASE_URL unset for local SQLite, or point it at a Postgres URL
DATABASE_URL="postgresql://..."
```

## Running locally

```bash
uvicorn main:app --reload
```

Visit `http://127.0.0.1:8000/docs` for interactive API docs.

## Seeding data

```bash
python seed.py
```

Generates 15 facilities (major Indian cities), 20 doctors per facility (2 per department), and a full day of 30-minute appointment slots (9am–5pm) for each doctor. Safe to point `DATABASE_URL` at Neon before running to seed production too.

## API Overview

| Tag | Endpoints |
|---|---|
| **Facilities** | `GET /facilities` (filter by accessibility/language), `GET /facilities/{id}` |
| **Doctors** | `GET /doctors` (filter by facility/department) |
| **Appointment Slots** | `GET /slots`, `GET /slots/booked`, `POST /slots/{id}/book`, `POST /waitlist` |
| **Auth** | `POST /signup`, `POST /login` |
| **Appointments** | `GET /appointments`, `PATCH /appointments/{id}/reschedule`, `POST /appointments/{id}/cancel` |
| **Checklist** | `PATCH /checklist` |

Full request/response schemas are available at `/docs`.

## Notes

- Auth is intentionally minimal: `POST /login` returns a `user_id`, which the frontend reuses on later requests. No tokens/sessions — a deliberate scope choice for the hackathon, not an oversight.
- Booking is race-safe: an atomic `UPDATE ... WHERE is_available = True` guarantees no slot is ever double-booked, even under concurrent requests.
- Cancelling a booked slot automatically reassigns it to the oldest waitlist entry for that slot, if one exists, instead of just reopening it.
