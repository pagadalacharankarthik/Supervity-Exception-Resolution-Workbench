# Technology Stack

## Stack Overview

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND                              │
│                                                         │
│  React 19      — UI component framework                 │
│  TypeScript    — Type safety across all components      │
│  Vite          — Ultra-fast dev server & bundler        │
│  TailwindCSS   — Utility-first styling                  │
│  Lucide Icons  — Consistent icon system                 │
│  React Router  — Client-side routing / SPA navigation   │
│                                                         │
│  Hosted on: Vercel (free CDN, global edge)              │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                     BACKEND                             │
│                                                         │
│  FastAPI       — High-performance async REST API        │
│  Uvicorn       — ASGI server (production-grade)         │
│  SQLAlchemy    — ORM with session management            │
│  Pydantic v2   — Schema validation & serialization      │
│  Python-JOSE   — JWT token authentication               │
│  Passlib/bcrypt— Password hashing                       │
│  Python-dotenv — Environment variable loading           │
│                                                         │
│  Hosted on: Render.com (free web service)               │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    DATABASE                             │
│                                                         │
│  SQLite  — Default (local dev + Render free tier)       │
│  PostgreSQL — Production upgrade path                   │
│  Auto-fallback: psycopg2 unavailable → SQLite           │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   AI / LLM LAYER                        │
│                                                         │
│  MockLLMProvider — Default, offline, deterministic      │
│  OpenAI (GPT-4)  — Plug-in via OPENAI_API_KEY env var  │
│  Google Gemini   — Plug-in via GEMINI_API_KEY env var  │
│                                                         │
│  All providers implement the same LLMProvider interface │
│  — swappable without changing application logic         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                  DEVOPS / TOOLING                       │
│                                                         │
│  Docker Compose  — Local PostgreSQL database service    │
│  pytest          — Backend unit + integration tests     │
│  Git / GitHub    — Version control & CI trigger         │
│  Vercel CLI      — Frontend deployment                  │
│  Render          — Backend deployment                   │
└─────────────────────────────────────────────────────────┘
```

---

## Why Each Technology Was Chosen

### FastAPI (Backend Framework)
- Automatic OpenAPI/Swagger documentation at `/docs`
- Native async support for non-blocking I/O
- Pydantic-native request/response validation
- 10x faster than Flask for data-heavy APIs

### SQLAlchemy ORM
- Database-agnostic — same code works with SQLite and PostgreSQL
- Session management with automatic rollback on errors
- Relationship loading (lazy + eager) for complex evidence packages

### React 19 + TypeScript
- Strict TypeScript typing prevents runtime errors at the interface boundary
- React 19's improved rendering for real-time status updates
- Component-based architecture enables reusable exception cards and status badges

### MockLLMProvider (Default AI)
- Enables 100% offline operation — no API key required for demo/testing
- Deterministic responses allow reproducible CI/CD test runs
- Grounded in actual DB evidence — not hallucinated
- Instantly swappable for real OpenAI/Gemini with a single env var change

### SQLite → PostgreSQL Fallback Pattern
- Zero configuration for local development
- No external database required for evaluation/demo
- Production path to PostgreSQL via single `DATABASE_URL` env var change

### JWT Authentication
- Stateless — no server-side session storage required
- Role-based (`reviewer` vs `manager`) claims embedded in token
- LocalStorage token persistence for seamless page refresh

---

## Environment Variables

| Variable | Service | Purpose |
|---|---|---|
| `DATABASE_URL` | Backend | PostgreSQL connection string (optional — falls back to SQLite) |
| `OPENAI_API_KEY` | Backend | Enable OpenAI GPT-4 LLM provider |
| `GEMINI_API_KEY` | Backend | Enable Google Gemini LLM provider |
| `FRONTEND_URL` | Backend | CORS allowed origin for deployed frontend |
| `VITE_API_URL` | Frontend | Backend API base URL (baked in at build time) |
| `SECRET_KEY` | Backend | JWT signing secret |
