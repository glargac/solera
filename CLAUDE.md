# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Backend (from `backend/`): `.venv/bin/uvicorn app.main:app --reload`; tests `.venv/bin/pytest`; one test `.venv/bin/pytest tests/test_api.py::test_parse_ical`
- Frontend (from `frontend/`): `npm run dev`, tests `npm test` (one file: `npx vitest run src/pages/Login.test.tsx`), coverage `npm run coverage`, `npx tsc -b` (typecheck), `npx vite build`

## Testing notes
- Backend: `backend/.coveragerc` needs `concurrency = greenlet,thread` or async SQLAlchemy code is reported as uncovered. Outbound HTTP (iCal, Supabase Storage, JWKS) is mocked with `httpx.MockTransport` (see `tests/test_external.py`); `tests/helpers.py` has `make_user/make_property/make_booking`.
- Frontend: `src/test/setup.ts` mocks `lib/supabase` globally and loads fake-indexeddb; pages are tested by spying on `api` from `lib/api` and rendering with `renderWithProviders` (`src/test/utils.tsx`).

## Architecture
- Monorepo: `backend/` FastAPI + SQLModel (async), `frontend/` React + TS + Tailwind 3 PWA. Auth is Supabase: the frontend logs in with supabase-js and sends the access token; `backend/app/core/security.py` validates it against the project JWKS (`SUPABASE_URL/auth/v1/.well-known/jwks.json`, ES256/RS256, keys cached by `kid`) and auto-creates a `User` row (role `host`) on first request.
- Use `sqlmodel.ext.asyncio.session.AsyncSession` (not SQLAlchemy's) — endpoints rely on `session.exec`.
- Bookings come from manual entry or iCal sync (`services/ical_sync.py`, scheduled via APScheduler in `main.py` lifespan, upsert by `(property_id, external_uid)`). Creating/syncing a booking calls `services/cleaning_tasks.ensure_cleaning_task` which creates the checkout-day `CleaningTask` (skipped for `personal` bookings).
- Cleaning tasks need 3 photos (uploaded to Supabase Storage via `services/storage.py`) before they can be completed. Frontend queues photos offline in IndexedDB (`frontend/src/lib/photoQueue.ts`).
- Guest guide is public, keyed by `Booking.guide_token` (`/api/v1/guests/guide/{token}`, route `/guide/:token`).
- Ownership scoping: every host endpoint filters by `Property.owner_id == user.id`; tests in `backend/tests/test_api.py` cover isolation.
- AI agents are planned under `backend/app/services/ai/` (Anthropic SDK, no LangChain for now; LangChain may be added later).
- Tests use in-memory SQLite and a self-signed JWT (`tests/conftest.py`).
- Tables are created with `create_all` at startup; Alembic is not set up yet.
