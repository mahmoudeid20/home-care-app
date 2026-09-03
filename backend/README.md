# HomeCare Backend

FastAPI backend for the HomeCare home-nursing marketplace. Phase 1 (this
delivery) implements authentication end-to-end: registration, login,
JWT access/refresh tokens with rotation, logout, and password reset.

## Requirements

- Python 3.12+
- Docker & Docker Compose (recommended for local dev)
- PostgreSQL 16 (via Docker Compose, or your own instance)
- Redis 7 (via Docker Compose, or your own instance)

## Quick start (Docker Compose — recommended)

From the **monorepo root** (`homecare/`):

```bash
cp backend/.env.example backend/.env
# edit backend/.env and set real JWT_SECRET / JWT_REFRESH_SECRET values

docker compose up --build
```

This starts Postgres, Redis, and the API (with auto-reload), running
Alembic migrations automatically before the server starts.

- API: http://localhost:8000
- Swagger docs: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc
- Health check: http://localhost:8000/health

## Running locally without Docker

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# point DATABASE_URL / REDIS_URL at your local Postgres/Redis instances

alembic upgrade head
uvicorn app.main:app --reload
```

## Database migrations

Migrations are managed with Alembic (`migrations/`).

```bash
# apply all migrations
alembic upgrade head

# create a new migration after changing models
alembic revision --autogenerate -m "add patients table"

# roll back one migration
alembic downgrade -1
```

## Running tests

Tests use an in-memory SQLite DB and a fake Redis, so no external services
are required:

```bash
cd backend
pytest -v
```

All 145 tests should pass (13 auth + 16 profiles + 14 care requests + 14
matching/search + 21 applications/bookings + 11 chat + 13 reviews/
notifications + 26 admin/complaints/payments + 9 security + 8 AI
extraction), covering happy paths, RBAC boundaries, ownership checks,
validation errors, state-machine edge cases, real-time WebSocket
delivery, security controls, and defensive handling of untrusted/
malformed LLM output.

## Seed data

`python -m app.seed` (Section 40) seeds a complete, immediately-testable
dataset: 5 specialties, 10 services, 10 nurses (7 approved+verified, 3
pending — so the admin verification queue isn't empty on first run), 5
patients, 5 care requests across different statuses (OPEN/MATCHED/CLOSED/
CANCELLED), 3 bookings (REVIEWED with a real 5-star review whose comment
and rating are reflected in the nurse's aggregate — not an unrelated
random number, ACTIVE, CONFIRMED), and one admin account.

It's idempotent (checks for `admin@homecare.example` first, so re-running
against an already-seeded database is a safe no-op) and was verified
end-to-end against a real running instance in this project — not just
executed once and assumed correct: logging in as a seeded patient and
nurse, browsing the marketplace (confirmed only the 7 approved nurses are
visible, matching Section 17's gate), checking the admin's pending-
verification queue (confirmed exactly the 3 unapproved nurses), and
confirming the seeded review's rating flows through to the nurse's public
profile.

Logins: `admin@homecare.example` / `AdminPass123`,
`nurse1..nurse10@homecare.example` / `NursePass123`,
`patient1..patient5@homecare.example` / `PatientPass123`.

## Project layout

```
app/
  core/        # config, db engine, security (hashing/JWT), redis, exceptions
  models/      # SQLAlchemy ORM models
  schemas/     # Pydantic request/response schemas
  api/         # routers (thin) + shared dependencies (auth guards)
  services/    # business logic
  repositories/# DB access layer
  websocket/   # (Phase 6: chat)
  tasks/       # (background jobs, future phases)
  utils/
migrations/    # Alembic
tests/         # pytest suite
```

## What's implemented in Phase 1

- `POST /api/v1/auth/register` — create PATIENT or NURSE account (ADMIN
  cannot self-register)
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh` — rotates refresh tokens; old token is
  blacklisted in Redis on use
- `POST /api/v1/auth/logout` — blacklists the refresh token
- `POST /api/v1/auth/forgot-password` — always returns 204 (no user
  enumeration); generates a reset token (delivery via email/SMS is a
  future integration point, logged to console in dev)
- `POST /api/v1/auth/reset-password`
- `GET /api/v1/auth/me`
- RBAC dependency (`require_roles`) ready for use by every future
  domain router
- Consistent JSON error envelope: `{"error": {"code": ..., "message": ...}}`
- Passwords hashed with bcrypt, never returned in any response
- `users` table + Alembic migration `0001_create_users_table`

## What's implemented in Phase 2

- `POST /api/v1/patients/me`, `GET /api/v1/patients/me`, `PATCH /api/v1/patients/me`
- `POST /api/v1/nurses/me` (onboarding), `GET/PATCH /api/v1/nurses/me`,
  `GET /api/v1/nurses/{id}` (public profile)
- `POST /api/v1/nurses/me/documents`, `GET /api/v1/nurses/me/documents`
  (verification document metadata — status starts `PENDING`)
- `GET /api/v1/specialties`, `GET /api/v1/services` (admin-configurable
  catalogs, never hard-coded client-side)
- `locations`, `specialties`, `services`, `patients`, `nurses`,
  `nurse_specialties`, `nurse_services`, `nurse_availability`,
  `nurse_documents` tables + Alembic migration `0002_add_profiles`
- Verification badges (`identity_verified`, `qualification_verified`,
  `experience_verified`) and `is_approved` all default `false` — only an
  admin (Phase 8) can flip them

## What's implemented in Phase 3

- `POST /api/v1/care-requests` — full 6-step request in one call (patient
  info, required services, nurse requirements, location, schedule, budget)
- `GET /api/v1/care-requests` (list mine), `GET /api/v1/care-requests/{id}`
  (owner-only), `PATCH /api/v1/care-requests/{id}` (owner-only, OPEN status
  only), `POST /api/v1/care-requests/{id}/cancel`
- `care_requests`, `care_request_services`, `care_request_specialties`,
  `care_request_requirements` tables + Alembic migration
  `0003_add_care_requests`
- Server-side status machine (`OPEN → MATCHED → CLOSED/EXPIRED/CANCELLED`)
  — the client can never set status directly; `MATCHED` will only be set by
  the booking service in Phase 5
- Budget/hours stored as numeric columns, never formatted strings
- The endpoint never diagnoses or interprets the medical condition text —
  it's stored and surfaced as-is for nurses/admins to read (Section 2's
  healthcare-safety boundary)

## What's implemented in Phase 4

- `GET /api/v1/nurses` — marketplace browse/search (Sections 14-15) with
  server-side filters: gender, min experience, specialty, min rating, price
  range + payment frequency, shift availability, verification status,
  governorate. Only approved, non-suspended nurses are ever returned.
- `GET /api/v1/care-requests/{id}/matches` — rule-based ranked
  recommendations (Section 21): skills 30%, experience 20%,
  location/distance 15%, availability 15%, price 10%, rating 5%,
  verification 5%. Hard filters exclude unapproved/suspended nurses and
  (when set) enforce `verified_nurses_only` and `preferred_nurse_gender`.
  Each result includes `match_score`, `distance_km` (haversine when both
  sides have coordinates, else a coarse governorate/city fallback),
  `estimated_price`, and human-readable `matching_reasons`.
- `GET/PATCH /api/v1/admin/matching-weights` (ADMIN only) — weights are
  DB-backed and editable, never hard-coded; PATCH validates they sum to 1.0
- `matching_weights` table + Alembic migration `0004_add_matching_weights`
- The engine only ranks fit — it never evaluates, comments on, or reasons
  about the patient's medical condition (Section 2's healthcare-safety
  boundary holds through matching too)

## What's implemented in Phase 5

- `POST /api/v1/applications` — patient sends a care request to a specific
  nurse (Section 11). Requires an OPEN care request owned by the caller and
  an approved, non-suspended nurse; blocks duplicate pending requests to
  the same nurse for the same care request.
- `GET /api/v1/applications/received` (nurse's "New Requests", Section 18),
  `GET /api/v1/applications/sent` (patient's view)
- `POST /api/v1/applications/{id}/accept` — atomically: marks the
  application ACCEPTED, **creates a Booking**, moves the care request to
  MATCHED, and auto-rejects every other still-pending application for that
  same care request (Section 45's flow, end to end)
- `POST /api/v1/applications/{id}/reject`, `POST /api/v1/applications/{id}/withdraw`
- `GET /api/v1/bookings` (mine, patient or nurse), `GET /api/v1/bookings/{id}`
- Booking state machine (Section 19), enforced server-side with an explicit
  allowed-transitions-per-role map — **the client can never set status
  directly**:
  - `POST /bookings/{id}/confirm` — PATIENT only, `ACCEPTED → CONFIRMED`
  - `POST /bookings/{id}/start` — NURSE only, `CONFIRMED → ACTIVE`
  - `POST /bookings/{id}/complete` — NURSE only, `ACTIVE → COMPLETED`
  - `POST /bookings/{id}/cancel` — either party, only from `ACCEPTED`/`CONFIRMED`;
    reopens the care request to `OPEN` so the patient can pick another nurse
  - `COMPLETED → REVIEWED` is reserved for the review service (Phase 7),
    never a direct client action
- `applications`, `bookings` tables + Alembic migration
  `0005_add_applications_bookings`
- Booking terms (dates, hours, payment frequency, agreed price) are
  snapshotted at booking-creation time so later edits never retroactively
  change an active booking

## What's implemented in Phase 6

- `POST /api/v1/conversations` — start (or idempotently resume) a
  conversation with a nurse, mirroring the "Message" button on a nurse's
  public profile (Section 16). No booking required first.
- `GET /api/v1/conversations` — list mine with the other party's name and
  a last-message preview, sorted by recency (patient or nurse view)
- `GET /api/v1/conversations/{id}/messages` (paginated), `POST /api/v1/conversations/{id}/messages`
  (REST fallback for sending — used for attachments already uploaded to
  storage, or when a socket isn't connected)
- **`WS /ws/conversations/{id}?token=<access_token>`** — real-time delivery.
  Token passed as a query param since browsers can't set WS handshake
  headers; every connection is authorized against the same participant
  check as the REST endpoints before being accepted, and every message
  a client sends is persisted through the same `ChatService.send_message`
  path REST uses, then broadcast to whichever other participant(s) are
  currently connected to that conversation.
- Supports `TEXT`, `IMAGE`, and `FILE` message types (image/file messages
  reference an already-uploaded `attachment_url`); the schema is left open
  for voice messages/calls and video calls (Section 20) without needing to
  change the `Conversation` shape later.
- Authorization is strict: only the two participants (or nobody else) can
  read or write in a conversation — enforced once in `ChatService`, reused
  identically by REST and WebSocket
- `conversations`, `messages` tables + Alembic migration `0006_add_chat`
- In-memory single-instance connection registry for broadcast, with a
  documented swap-in point for Redis pub/sub once running multi-instance
  (Section 20: "Redis if required for realtime infrastructure")

## What's implemented in Phase 7

- `POST /api/v1/reviews` — patient reviews a nurse after a `COMPLETED`
  booking (Section 24): overall/professionalism/communication/care-quality
  ratings (1-5) + optional comment. Transitions the booking to `REVIEWED`,
  closing Phase 5's state machine loop, and atomically recomputes the
  nurse's denormalized `average_rating`/`review_count` used everywhere else
  (search, matching, public profile).
- `GET /api/v1/nurses/{id}/reviews` — public review list for a nurse's
  profile page (Section 16)
- Duplicate-review prevention: a unique DB constraint on `booking_id` is
  the backstop, checked explicitly in the service layer first so a repeat
  attempt returns a precise `409` rather than a generic status error
- `GET /api/v1/notifications` (in-app notification center),
  `GET /api/v1/notifications/unread-count`,
  `POST /api/v1/notifications/{id}/read`
- Every record from Section 25's trigger list now actually fires, wired
  into the services built in earlier phases rather than left as a stub:
  new request (nurse), request accepted/rejected (patient and any
  auto-rejected other nurses), booking confirmed/cancelled (the other
  party), new message (the other participant), new review (the nurse).
  `Booking reminder` and `Document verification result` are wired into
  `NotificationService` and ready to call, pending the scheduled-job
  infrastructure and the admin verification endpoint (Phase 8) respectively.
- Every notification is persisted to `notifications` first, then a push is
  attempted through `FCMClient` — currently a documented stub that logs
  what it would send, since real delivery needs a Firebase service-account
  credential that doesn't belong hard-coded into an MVP scaffold; swapping
  in `firebase-admin` is a one-file change (see `app/services/fcm_client.py`)
- `reviews`, `notifications` tables + Alembic migration
  `0007_add_reviews_notifications`

## What's implemented in Phase 8

Backend admin APIs only (Sections 26-31) — the Next.js admin **web app**
itself is not yet built; that's the remaining piece of the original Phase
8 scope, tracked separately since it's a different codebase
(`admin-dashboard/`) rather than more backend endpoints.

- **User management**: `GET /admin/users` (filter by role),
  `POST /admin/users/{id}/deactivate` / `/activate` — a deactivated user's
  next login attempt is rejected immediately
- **Nurse verification** (Section 17/28), fully audit-logged:
  - `GET /admin/nurses` (filter by approval/pending-verification status)
  - `GET /admin/nurses/{id}/documents`,
    `POST /admin/nurses/{id}/documents/{doc_id}/approve` (flips the
    matching `identity_verified`/`qualification_verified`/`experience_verified`
    flag), `.../reject` (with a reason)
  - `POST /admin/nurses/{id}/approve` — requires all three flags true first
    (422 otherwise); `.../suspend` / `.../reactivate` — a suspended nurse
    immediately disappears from marketplace search and matching
  - Every action notifies the nurse (`DOCUMENT_VERIFICATION_RESULT`) and
    writes an `admin_actions` row
- **Catalog management**: `GET/POST`/`PATCH /admin/services` and
  `/admin/specialties` — the lists patients and nurses pick from
  (Section 9) are genuinely admin-editable now, not just seeded. The admin
  `GET` returns inactive items too (unlike the public `/services` and
  `/specialties` endpoints), so a deactivated item can still be found and
  reactivated
- **Commission settings** (Section 31): `GET`/`PATCH /admin/settings`
  (`commission_percentage`, defaults to 10%)
- **Payments** (Section 30): a `Payment` row is created automatically —
  status `PENDING` — the moment a booking is marked `COMPLETED`, splitting
  the agreed price into `platform_commission`/`nurse_earnings` using the
  configured commission percentage. `GET /bookings/{id}/payment` (booking
  owner), `GET /admin/payments` (list all), `POST /admin/payments/{id}/mark-paid`
  (manual cash/external tracking — Section 30 explicitly forbids faking a
  successful confirmation automatically)
- **Complaints** (Section 29): `POST/GET /complaints` (patient or nurse,
  own complaints only), `GET/PATCH /admin/complaints` (admin triage with
  status + response, audit-logged)
- **Stats** (Section 27): `GET /admin/stats` — patient/nurse counts,
  verified/pending counts, booking counts by state, total revenue and
  commission earned (from `PAID` payments only), average rating, most
  requested services
- New tables: `admin_actions`, `platform_settings`, `payments`,
  `complaints` + Alembic migration `0008_add_admin_tables`

## What's implemented in Phase 9

Closes out the remaining unaddressed items from Section 32's security
checklist (most items — password hashing, JWT, RBAC, input validation,
authorization checks, no secrets in code — were already in place from
earlier phases; this phase adds what wasn't yet covered).

- **Rate limiting**: a Redis-backed fixed-window limiter (`INCR`+`EXPIRE`,
  60s window, `RATE_LIMIT_PER_MINUTE` in settings) applied globally via
  middleware, keyed by authenticated user id when available (fairer than
  pure IP-based limiting — one heavy user doesn't block others behind the
  same NAT), falling back to client IP for anonymous requests. Returns
  `429` with a `Retry-After` header. `/health` and the docs routes are
  exempt so monitoring/tooling isn't affected.
- **Secure HTTP headers** on every response (including error responses):
  `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`,
  `Permissions-Policy`, `Content-Security-Policy`
- **CORS hardening**: `allow_credentials` is automatically disabled when
  `CORS_ORIGINS` is still the wildcard `["*"]` — combining a wildcard
  origin with credentials is both rejected by browsers and an unsafe
  configuration if it ever did work
- **File type validation** for nurse verification documents and chat
  attachments: extension allowlisting (documents: pdf/jpg/jpeg/png/doc/docx;
  chat images: jpg/jpeg/png/gif/webp) rejects obviously wrong or dangerous
  file types before the reference is persisted. Documented honestly as a
  partial mitigation — real content-type sniffing and file size limits
  need actual file bytes, which belongs in the upload endpoint of whatever
  storage service issues these URLs (this MVP only stores references, it
  never handles raw uploads)
- New `tests/test_security.py` (9 tests): headers present on success *and*
  error responses, rate limiting triggers and is per-identity (not a
  global bucket), file extension validation on both document and chat
  attachment paths, CORS/credentials interaction

## What's implemented in Phase 10

AI requirement extraction (Section 22): the patient writes a free-text
description; an LLM extracts structured scheduling/demographic/care-type
fields, feeding the *same* matching engine built in Phase 4 — no changes
needed there.

- `POST /care-requests/extract` (PATIENT only) — takes free text, returns
  a pre-fill draft (age, gender, duration, hours/day, preferred shift,
  languages, mobility status, matched specialty/service IDs). **Never
  creates a care request itself** — the patient reviews and edits before
  calling the normal `POST /care-requests`, exactly as if they'd filled
  out the multi-step form by hand.
- Uses the real Anthropic SDK (`app/services/llm_client.py`,
  `AnthropicLLMClient`) with a system prompt that explicitly and
  repeatedly forbids diagnosis, treatment suggestions, or any clinical
  commentary — it extracts logistics keywords only (e.g. "post-operative",
  "elderly care"), never interprets medical meaning (Section 2's
  healthcare-safety boundary, restated for this specific call).
- Every field from the model is treated as **untrusted input**:
  `AIExtractionService` range-clamps numbers, validates enums against the
  real allowed values, and resolves specialty/service keywords against the
  actual catalog rather than trusting IDs from the model — so a
  hallucinated or malformed response can never introduce data the rest of
  the system hasn't already validated through its normal paths.
- Fails safe and fails clearly: non-JSON model output → empty extraction
  (never a crash); no `LLM_API_KEY` configured → a precise
  `AI_NOT_CONFIGURED` error rather than a generic 500.
- Fully tested (8 tests) against a `FakeLLMClient` injected via
  `app.dependency_overrides` (the same pattern as Redis in every other
  phase) — no real API key or network call needed to verify the logic,
  including a test that a model trying to sneak a `"diagnosis"` field
  into its output can't get it into the response (the schema simply
  doesn't have room for it).

## Next phases

See `/docs/ARCHITECTURE.md` at the monorepo root for the full roadmap
(Patient/Nurse profiles → Care requests → Matching → Bookings → Chat →
Reviews/Notifications → Admin dashboard → Security hardening → AI
matching).
