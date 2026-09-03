# HomeCare — Architecture & Roadmap

## 1. System Overview

HomeCare is a modular monolith backend (FastAPI) serving two clients:
- **Mobile app** (Flutter) — patients & nurses
- **Admin dashboard** (web) — platform administrators

```
┌─────────────┐     ┌─────────────┐
│  Flutter    │     │   Admin     │
│  Mobile App │     │  Dashboard  │
└──────┬──────┘     └──────┬──────┘
       │   HTTPS / WSS     │
       └─────────┬─────────┘
                  │
          ┌───────▼────────┐
          │   FastAPI       │
          │  (modular       │
          │   monolith)     │
          │                 │
          │  api/ (routers) │
          │  services/      │
          │  repositories/  │
          │  websocket/     │
          │  tasks/         │
          └───┬─────────┬───┘
              │         │
       ┌──────▼───┐ ┌───▼─────┐
       │ Postgres │ │  Redis  │
       │ (+pgvec  │ │ (cache, │
       │  future) │ │  pubsub)│
       └──────────┘ └─────────┘
```

Design principles applied from the spec:
- **Modular monolith**, not microservices (Section 48) — routers/services/repositories are cleanly separated per domain so services can be extracted later if needed.
- **No hard-coded business data** — specialties, services, and matching weights live in the DB / config, not in code (Sections 21, 9).
- **Backend is the source of truth for state machines** — booking/request status transitions are validated server-side only (Section 19).
- **AI is scoped strictly to matching/extraction**, never diagnosis (Section 2, 22).

## 2. Entity-Relationship Diagram (textual)

```
users (id PK, role, email, phone, password_hash, is_active, created_at, updated_at)
  │ 1:1
  ├── patients (id PK, user_id FK→users, full_name, ... )
  │      │ 1:N
  │      └── care_requests (id PK, patient_id FK, status, ...)
  │             │ 1:N                         │ 1:N
  │             ├── care_request_requirements  ├── applications (nurse_id FK)
  │             │      (id PK, care_request_id FK, key, value)
  │             └── bookings (id PK, care_request_id FK, nurse_id FK, status, ...)
  │
  └── nurses (id PK, user_id FK→users, title, experience_years, ...)
         │ 1:N
         ├── nurse_documents (id PK, nurse_id FK, type, status, reviewed_by FK→users)
         ├── nurse_specialties (nurse_id FK, specialty_id FK)  [M:N join]
         ├── nurse_services (nurse_id FK, service_id FK, price, unit)  [M:N join + attrs]
         ├── nurse_availability (id PK, nurse_id FK, day_of_week/date, start_time, end_time)
         ├── applications (id PK, care_request_id FK, nurse_id FK, status)
         └── bookings (id PK, ...)

specialties (id PK, name_en, name_ar, is_active)
services (id PK, name_en, name_ar, is_active)          -- configurable from admin (Sec 9)

bookings (id PK, care_request_id FK, patient_id FK, nurse_id FK, status,
          start_date, end_date, hours_per_day, payment_frequency,
          agreed_price, created_at, updated_at)
  │ 1:1
  ├── payments (id PK, booking_id FK, amount, currency, status, commission, nurse_earnings)
  │ 1:N (only after COMPLETED)
  └── reviews (id PK, booking_id FK UNIQUE, patient_id FK, nurse_id FK,
               overall_rating, professionalism, communication, care_quality, comment)

conversations (id PK, patient_id FK, nurse_id FK, booking_id FK nullable, created_at)
  │ 1:N
  └── messages (id PK, conversation_id FK, sender_id FK→users, type, content, attachment_url, created_at)

locations (id PK, governorate, city, area, lat, lng)  -- referenced by patients & nurses

notifications (id PK, user_id FK→users, type, title, body, data JSON, read_at, created_at)

complaints (id PK, user_id FK→users, booking_id FK nullable, category, description,
            status, admin_response, created_at)

admin_actions (id PK, admin_id FK→users, action_type, target_type, target_id,
               reason, created_at)   -- audit log (Sec 28)
```

Full SQLAlchemy models with indexes/constraints are implemented incrementally per phase (see backend/app/models).

## 3. Request/Booking State Machine (Section 19)

```
care_request: DRAFT → OPEN → MATCHED → CLOSED / EXPIRED / CANCELLED
application:  PENDING → ACCEPTED / REJECTED / WITHDRAWN
booking:      PENDING → ACCEPTED → CONFIRMED → ACTIVE → COMPLETED → REVIEWED
                    ↘ REJECTED      ↘ CANCELLED           ↘ EXPIRED
```
All transitions validated server-side in `services/booking_service.py` via an explicit
allowed-transitions map — never trust client-supplied status (enforced in Phase 5).

## 4. Matching Engine (Section 21)

Rule-based, weights loaded from `matching_weights` config table (DB-backed, admin-editable),
not hard-coded:

| Factor        | Default Weight |
|----------------|---------------|
| Skills match   | 30% |
| Experience     | 20% |
| Location/distance | 15% |
| Availability   | 15% |
| Price compatibility | 10% |
| Rating         | 5% |
| Verification   | 5% |

Implemented in `services/matching_service.py`, exposed via `GET /care-requests/{id}/matches`.
AI/LLM requirement-extraction (Phase 10) feeds the *same* structured schema this engine
already consumes — so Phase 10 requires no matching-engine changes, only a new
`services/ai_extraction_service.py` producing the same DTO.

## 5. Implementation Roadmap (mirrors Section 44)

| Phase | Scope | Status |
|---|---|---|
| 1 | Auth (register/login/refresh/logout, RBAC, password hashing) | **Done** — 13 tests passing |
| 2 | Patient & Nurse profiles | **Done** — 16 tests passing |
| 3 | Care requests (multi-step creation) | **Done** — 14 tests passing |
| 4 | Nurse search + rule-based matching | **Done** — 14 tests passing |
| 5 | Applications + bookings + state machine | **Done** — 21 tests passing |
| 6 | Chat (WebSocket) | **Done** — 11 tests passing |
| 7 | Reviews + notifications (FCM) | **Done** — 13 tests passing |
| 8 | Admin dashboard backend | **Done** — 26 tests passing |
| 9 | Security hardening | **Done** — 9 tests passing |
| — | Admin dashboard web UI (Next.js) | **Done** — builds clean, lints clean, smoke-tested against a live backend |
| 10 | AI matching | **Done** — 8 tests passing |
| — | Flutter mobile app | Not started (blocked: pub.dev unreachable in this environment) |
| 4 | Nurse search + rule-based matching | Planned |
| 5 | Applications + bookings + state machine | Planned |
| 6 | Chat (WebSocket) | Planned |
| 7 | Reviews + notifications (FCM) | Planned |
| 8 | Admin dashboard (web) | Planned |
| 9 | Security hardening + full test suite | Planned |
| 10 | AI matching (LLM requirement extraction) | Planned |

Each phase will list the exact files touched before implementation, per your Section 44/50
requirements. Mobile (Flutter) screens are built alongside the backend phase they depend on,
starting from Phase 1 (auth screens) once the auth API is working and tested.

## 6. Tech Stack (confirmed, per Section 3–4)

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2, PostgreSQL 16, Redis 7, JWT (python-jose), passlib[bcrypt], WebSockets, pytest.
- **Mobile**: Flutter, Riverpod, GoRouter, Dio, flutter_secure_storage, firebase_messaging.
- **Admin**: Next.js (React) — chosen for fast CRUD/table-heavy admin screens with server components; kept in `admin-dashboard/` as a separate deployable, calling the same REST API.
- **Infra**: Docker Compose (backend + postgres + redis) for local dev.
