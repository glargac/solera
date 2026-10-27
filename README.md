# SOLORA App

SaaS de gestión de alquileres turísticos (Costa del Sol). Monorepo: `backend/` (FastAPI) y `frontend/` (React + Vite + Tailwind, PWA).

## Puesta en marcha

### 1. Supabase
Crea un proyecto en supabase.com y un bucket de Storage `cleaning-photos`. Copia URL, anon key, service key y JWT secret (Project Settings → API).

### 2. Backend
```bash
cd backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env        # rellena los valores
.venv/bin/uvicorn app.main:app --reload --port 8001   # http://localhost:8001/docs
.venv/bin/pytest
```
Sin `DATABASE_URL` de Postgres usa SQLite local (tablas creadas al arrancar).

### 3. Frontend
```bash
cd frontend
npm install
cp .env.example .env        # rellena los valores
npm run dev                 # http://localhost:5173
```

## Tests
```bash
cd backend  && .venv/bin/pytest --cov          # 34 tests, ~97% cobertura
cd frontend && npm test                          # 35 tests (Vitest + Testing Library)
cd frontend && npm run coverage                  # con informe de cobertura
```
La CI (`.github/workflows/ci.yml`) ejecuta ambos, el typecheck y el build en cada push y pull request.

## Pendiente
Alembic (migraciones), RLS en Supabase, asignación de limpiadores desde la UI, agentes de IA, registro de viajeros.
