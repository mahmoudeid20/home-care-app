# HomeCare

AI-assisted home-care nursing marketplace connecting patients / families
with verified nurses for home-based care in Egypt (architected to scale to
other markets).

> **Healthcare safety note**: this platform performs matching, search, and
> administrative automation only. It never diagnoses conditions, prescribes
> medication, or recommends treatment. See `docs/ARCHITECTURE.md` §2.

## Repository layout

```
homecare/
  backend/            FastAPI modular-monolith API (Phases 1-9 implemented)
  mobile/             Flutter app (patient + nurse) — not yet started
  admin-dashboard/    Admin web app (Next.js) — implemented
  docs/
    ARCHITECTURE.md   Full architecture, ERD, roadmap
  docker-compose.yml  Local dev: backend + Postgres + Redis
```

## Status

**Backend Phases 1-10: 145/145 tests passing.** Auth, patient/nurse
profiles, care requests, rule-based matching, nurse search, applications &
bookings (full state machine), real-time WebSocket chat, reviews,
notifications, the admin backend (user management, nurse verification
with audit logging, catalog CRUD, commission settings, payments,
complaints, dashboard stats), a security-hardening pass (rate limiting,
secure headers, file-type validation, CORS hardening), and AI requirement
extraction (real Anthropic SDK integration, defensive against untrusted
LLM output, never diagnoses).

**Admin dashboard (Next.js): built and verified end-to-end.** Login,
platform overview/stats, user management, the full nurse verification
workflow (documents → approve/reject → approve nurse → suspend/
reactivate), services/specialties catalog, payments, complaints, and
settings (commission % + matching weights). `npm run build` and
`npm run lint` both pass clean, and the app was smoke-tested against a
real running backend (Postgres + Redis + FastAPI, not mocks) — login,
nurse listing, document approval, and stats all confirmed working over
real HTTP with CORS correctly configured, not just compiling.

**Not built**: the Flutter mobile app — the actual patient/nurse consumer
product, and the single biggest remaining piece. This environment can't
install or verify Flutter/Dart at all (pub.dev and the Flutter SDK's
download host are both unreachable here), which is why it wasn't
attempted: writing a large amount of unverifiable Dart code would
conflict with this project's practice of only shipping code that's
actually been proven to run. See `docs/ARCHITECTURE.md` for the full
roadmap.

## Getting started

```bash
cp backend/.env.example backend/.env
# set real JWT secrets in backend/.env
docker compose up --build
```

Then visit http://localhost:8000/api/v1/docs for interactive API docs.

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system architecture, ERD,
  state machines, matching engine design, phase roadmap
- [`backend/README.md`](backend/README.md) — backend setup, migrations,
  testing, endpoint reference for what's implemented so far
