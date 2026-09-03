# HomeCare Admin Dashboard

Next.js 16 (App Router) + TypeScript + Tailwind CSS v4 web app for platform
administrators — the frontend for the admin API built in backend Phase 8
(Sections 26-31).

## What's here

- **Login** — admin-only; a PATIENT/NURSE account signing in here is
  rejected client-side (the backend itself never issues them an admin
  session, this is just a friendlier error message)
- **Overview** — platform stats (Section 27): patient/nurse counts,
  verification counts, booking counts by state, revenue, commission
  earned, average rating, most-requested services
- **Users** — list, filter by role, activate/deactivate
- **Nurse verification** — the core workflow (Section 17/28): list
  pending/approved nurses, open a nurse to review their uploaded
  documents, approve/reject each one (which flips the matching
  identity/qualification/experience flag), approve the nurse once all
  three are verified, suspend/reactivate
- **Services & specialties** — catalog CRUD (Section 9), including
  reactivating previously-deactivated entries
- **Payments** — list by status, mark a pending payment paid (cash/bank
  transfer) once money has actually changed hands (Section 30)
- **Complaints** — triage, respond, change status (Section 29)
- **Settings** — commission percentage (Section 31) and the rule-based
  matching engine's weights (Section 21), with a live sum check

## Running it

Requires the backend (see `../backend/README.md`) running and reachable.

```bash
npm install
cp .env.local.example .env.local
# edit .env.local if the backend isn't at the default URL
npm run dev
```

Then visit http://localhost:3000. You'll need an admin account — the
backend has no self-registration for ADMIN by design (Section 7), so
create one directly in the database for local development:

```python
# from backend/, with the venv active
python -c "
import asyncio
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole

async def main():
    async with AsyncSessionLocal() as db:
        db.add(User(email='admin@example.com', password_hash=hash_password('ChangeMe123'), role=UserRole.ADMIN))
        await db.commit()

asyncio.run(main())
"
```

## Building for production

```bash
npm run build
npm start
```

Both were verified to complete cleanly (`npm run build`, `npm run lint`)
and the app was smoke-tested end-to-end against a real running backend
(Postgres + Redis + FastAPI) — login, the nurse-verification workflow
(list pending → view documents → approve each → approve the nurse),
and the stats page all confirmed working, not just compiling.

## Architecture notes

- **Auth**: JWT access/refresh tokens stored in `localStorage` (simplest
  approach for an internal tool; a production hardening pass would move
  to an httpOnly cookie issued by a Next.js route handler acting as a thin
  proxy, to keep tokens out of JS-accessible storage entirely). A 401
  triggers one automatic refresh attempt before giving up and redirecting
  to `/login`.
- **No server-side auth guard**: route protection is a client-side check
  in `(dashboard)/layout.tsx`. This is fine because the *data* is always
  protected server-side by the backend's RBAC — the frontend guard only
  prevents a flash of dashboard chrome before redirecting, it grants no
  actual access.
- **Design tokens** live in `src/app/globals.css` (Tailwind v4's CSS-first
  `@theme` config) — a deliberate teal/amber healthcare palette and a
  serif-display/sans-body/mono-numerals type system, not Tailwind's
  defaults. Fonts are system stacks rather than `next/font/google`, since
  the build must succeed in network environments without access to
  Google's font CDN (this was caught by actually running the build in
  this project's own sandbox).
