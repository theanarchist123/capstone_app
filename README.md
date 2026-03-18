
<h1 align="center">🩺 OnCopilot</h1>
<h3 align="center">Clinical AI · Precision Medicine · Reimagined</h3>

<p align="center">
  <strong>An AI-powered clinical decision-support platform for oncologists.</strong><br/>
  Biomarker-driven treatment pathways · NLP report extraction · Real-time analytics
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-E84A5F?style=for-the-badge&logo=semantic-release&logoColor=white" />
  <img src="https://img.shields.io/badge/license-MIT-2ECC71?style=for-the-badge" />
  <img src="https://img.shields.io/badge/status-active-27AE60?style=for-the-badge" />
  <img src="https://img.shields.io/badge/capstone-2026-8E44AD?style=for-the-badge" />
</p>

---

## ✨ What is OnCopilot?

> **OnCopilot** is a full-stack oncology co-pilot that turns raw biomarker data into ranked, evidence-based treatment plans — in seconds.

Doctors enter a patient case (biomarkers, genomic scores, comorbidities), upload PDF/DOCX lab reports, and the system automatically:

- 🔬 **Classifies** breast cancer subtype (ER/PR/HER2/Ki-67 → Luminal A/B, HER2+, TNBC)
- 🧬 **Modifies risk** via OncotypeDX, MammaPrint, BRCA genomic scoring
- 🛡️ **Flags** immune/mutation markers (PD-L1, TILs, PIK3CA, TP53…)
- 💊 **Generates** 2–4 ranked treatment protocols with clinical rule traces
- ⚠️ **Checks contraindications** — cardiac, renal, hepatic, ECOG, allergies
- 📄 **Exports** a signed clinical PDF report to Supabase Storage

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                  │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │             Next.js 14 (App Router) · TypeScript              │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │  │
│  │  │  Zustand │  │Framer    │  │ Recharts │  │  Radix UI   │  │  │
│  │  │  Store   │  │ Motion   │  │ Charts   │  │ Components  │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ HTTPS / REST (Axios)
┌───────────────────────────▼─────────────────────────────────────────┐
│                         API LAYER                                    │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              FastAPI (async) · Rate-Limited · CORS            │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │  │
│  │  │   Auth   │  │  Cases   │  │ Analysis │  │  Analytics  │  │  │
│  │  │  /auth/* │  │/cases/*  │  │/analyse  │  │/analytics/* │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────────┘  │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │  │
│  │  │ Reports  │  │   PDF    │  │Notifs    │  │2nd Opinion  │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                              │                                       │
│     ┌────────────────────────▼──────────────────┐                   │
│     │           CLINICAL ENGINE                 │                   │
│     │  Stage 1 → Subtype Classification         │                   │
│     │  Stage 2 → Genomic Risk Modifiers         │                   │
│     │  Stage 3 → Immune / Mutation Flags        │                   │
│     │  Stage 4 → Treatment Pathway Generator    │                   │
│     │  Stage 5 → Contraindication Safety Check  │                   │
│     └────────────────────────┬──────────────────┘                   │
│                              │                                       │
│     ┌────────────────────────▼──────────────────┐                   │
│     │       NLP PIPELINE (spaCy)                │                   │
│     │  PDF/DOCX → 13 Clinical Entity Extraction │                   │
│     └────────────────────────┬──────────────────┘                   │
│                              │                                       │
└──────────────────────────────┼──────────────────────────────────────┘
                               │ asyncpg / SQLAlchemy 2.0
┌──────────────────────────────▼──────────────────────────────────────┐
│                       DATA LAYER                                     │
│  ┌───────────────────────────┐  ┌─────────────────────────────────┐ │
│  │  PostgreSQL (Supabase)    │  │   Supabase Storage              │ │
│  │  9 tables · Alembic       │  │   Private bucket · Signed URLs  │ │
│  │  migrations · Audit logs  │  │   PDF/DOCX/TXT · 10 MB limit    │ │
│  └───────────────────────────┘  └─────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🧠 The Clinical Engine — 5-Stage Pipeline

The heart of OnCopilot lives in `backend/engine/biomarker_algorithm.py`:

| # | Stage | Function | What it does |
|---|-------|----------|-------------|
| 1 | **Subtype Classification** | `classify_subtype()` | Maps ER/PR/HER2/Ki-67 → Luminal A, Luminal B, HER2+, or TNBC via NCCN/St.Gallen criteria |
| 2 | **Genomic Risk Modifiers** | `genomic_risk_modifiers()` | Adjusts treatment aggressiveness using OncotypeDX RS, MammaPrint, and BRCA1/2 mutation status |
| 3 | **Immune & Mutation Flags** | `immune_mutation_flags()` | Evaluates PD-L1 expression, TIL density, PIK3CA, TP53, TOP2A, BCL2, Cyclin-D1 for targeted therapy eligibility |
| 4 | **Treatment Pathway Generation** | `generate_treatment_pathways()` | Produces 2–4 ranked protocols (e.g., AC→T, CDK4/6 + ET) with a human-readable rule trace per recommendation |
| 5 | **Contraindication Safety Check** | `check_contraindications()` | Enforces 6 safety rules — cardiac toxicity, renal function, hepatic capacity, ECOG performance score, drug allergies |

---

## 🗂️ Monorepo Structure

```
capstone_app/
│
├── 📁 src/                          ← Next.js App Router source
│   ├── app/
│   │   ├── page.tsx                 ← Landing / root
│   │   ├── login/                   ← Auth screens
│   │   ├── signup/
│   │   └── dashboard/               ← Main clinical dashboard
│   ├── components/                  ← Shared UI components (Radix-based)
│   ├── store/                       ← Zustand state stores
│   ├── lib/                         ← Utility functions, API client
│   └── types/                       ← TypeScript type definitions
│
├── 📁 backend/                      ← FastAPI Python backend
│   ├── main.py                      ← App entry, router registration
│   ├── core/
│   │   ├── config.py                ← Pydantic settings from .env
│   │   ├── security.py              ← JWT + bcrypt
│   │   └── database.py              ← Async SQLAlchemy engine
│   ├── api/
│   │   ├── deps.py                  ← JWT dependency + role guard
│   │   └── routes/                  ← 9 route modules
│   ├── engine/
│   │   ├── biomarker_algorithm.py   ← 5-stage clinical pipeline ⭐
│   │   ├── contraindication_checker.py
│   │   └── nlp_extractor.py         ← spaCy: 13 entity types
│   ├── services/
│   │   ├── case_service.py
│   │   ├── report_service.py
│   │   └── pdf_service.py           ← WeasyPrint PDF generation
│   ├── models/                      ← SQLAlchemy ORM (9 tables)
│   ├── schemas/                     ← Pydantic v2 schemas
│   ├── alembic/                     ← Async DB migrations
│   ├── scripts/seed.py              ← 50 anonymised dev cases
│   └── tests/                       ← Pytest + httpx test suite
│
├── package.json                     ← Next.js dependencies
├── tailwind.config.ts
├── next.config.mjs
└── .env.local                       ← Frontend environment
```

---

## 🛠️ Tech Stack

### Frontend
<p>
  <img src="https://skillicons.dev/icons?i=nextjs" height="40" title="Next.js 14" />
  <img src="https://skillicons.dev/icons?i=ts" height="40" title="TypeScript 5" />
  <img src="https://skillicons.dev/icons?i=tailwind" height="40" title="Tailwind CSS" />
  <img src="https://skillicons.dev/icons?i=react" height="40" title="React 18" />
  <img src="https://skillicons.dev/icons?i=vercel" height="40" title="Vercel" />
</p>

| Library | Role |
|---------|------|
| **Next.js 14** (App Router) | Full-stack React framework |
| **TypeScript 5** | Type-safe frontend |
| **Tailwind CSS** + shadcn/ui | Styling system |
| **Radix UI** | Accessible headless components |
| **Framer Motion** | Page transitions & micro-animations |
| **Zustand** | Lightweight global state |
| **Recharts** | Clinical data visualisation |
| **React Hook Form** + **Zod** | Form validation |
| **Axios** | HTTP client for API calls |
| **Sonner** | Toast notifications |

### Backend
<p>
  <img src="https://skillicons.dev/icons?i=python" height="40" title="Python 3.12" />
  <img src="https://skillicons.dev/icons?i=fastapi" height="40" title="FastAPI" />
  <img src="https://skillicons.dev/icons?i=postgres" height="40" title="PostgreSQL" />
  <img src="https://skillicons.dev/icons?i=supabase" height="40" title="Supabase" />
  <img src="https://skillicons.dev/icons?i=pytest" height="40" title="Pytest" />
</p>

| Library | Role |
|---------|------|
| **FastAPI** | Async REST API framework |
| **Pydantic v2** | Request/response validation |
| **SQLAlchemy 2.0 async** | ORM with asyncpg driver |
| **Alembic** | Database migrations |
| **Supabase** | PostgreSQL host + file storage |
| **PyJWT + bcrypt** | Authentication & token security |
| **spaCy** (`en_core_web_sm`) | NLP report entity extraction |
| **WeasyPrint** | HTML → PDF report generation |
| **slowapi** | Rate limiting middleware |
| **Pytest + httpx** | Async test suite |

---

## ⚡ Quick Start

### Prerequisites

| Tool | Minimum Version |
|------|----------------|
| Node.js | 18.x |
| Python | 3.11+ |
| npm / pnpm | 9.x |
| A Supabase project | (free tier works) |

---

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/your-username/capstone_app.git
cd capstone_app
```

---

### 2️⃣ Backend Setup

```bash
cd backend

# — Create & activate virtual environment —
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# — Install Python dependencies —
pip install -r requirements.txt

# — Download spaCy language model —
python -m spacy download en_core_web_sm
```

#### Configure Environment

```bash
# Copy the example env file
copy .env.example .env        # Windows
cp .env.example .env          # macOS / Linux
```

Open `.env` and fill in the following:

```env
# ── App ──────────────────────────────────────
APP_ENV=development
DEBUG=true
SECRET_KEY=your-super-secret-jwt-key-min-32-chars

# ── Supabase ─────────────────────────────────
SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-role-key
SUPABASE_BUCKET=reports

# ── Database ─────────────────────────────────
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# ── CORS ─────────────────────────────────────
ORIGINS=http://localhost:3002

# ── Rate Limiting ─────────────────────────────
RATE_LIMIT_PER_MINUTE=60
```

#### Run Migrations & Seed

```bash
# Apply all Alembic migrations
alembic upgrade head

# Seed 50 anonymised development cases
python scripts/seed.py
# Seed doctor login: seed.doctor@oncopilot.dev
```

#### Start the Backend

```bash
uvicorn main:app --reload --port 8000
```

> 🟢 API is live at `http://localhost:8000`  
> 📖 Interactive docs at `http://localhost:8000/docs`

---

### 3️⃣ Frontend Setup

```bash
# From the project root
cd ..

# Install dependencies
npm install
```

#### Configure Frontend Environment

```bash
copy .env.local.example .env.local     # Windows
cp .env.local.example .env.local       # macOS / Linux
```

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### Start the Frontend Dev Server

```bash
npm run dev
```

> 🟢 App is live at `http://localhost:3002`

---

### 4️⃣ Running Tests

```bash
cd backend

# Install the in-memory SQLite driver for tests
pip install aiosqlite

# Run the full test suite with coverage
pytest --cov=. --cov-report=term-missing
```

Test modules:

| File | Covers |
|------|--------|
| `tests/test_engine.py` | All 5 pipeline stages (unit) |
| `tests/test_auth.py` | Login, token refresh, RBAC |
| `tests/test_cases.py` | Case CRUD + full analysis integration |

---

## 🔐 Security Model

```
┌──────────────────────────────────────────────────────────────┐
│                     SECURITY LAYERS                          │
├──────────────────────────────────────────────────────────────┤
│  🔑  JWT Access Token       ──  15-minute expiry             │
│  🔄  JWT Refresh Token      ──  7-day expiry                 │
│  🔒  bcrypt password hashing                                 │
│  👤  Role-based access      ──  Doctors see only own cases   │
│  📝  Audit logging          ──  Every DB write is tracked    │
│  📁  File upload rules      ──  PDF/DOCX/TXT only, max 10 MB │
│  🌐  Signed URLs            ──  Private Supabase bucket      │
│  ⏱️  Rate limiting          ──  slowapi, per-IP              │
└──────────────────────────────────────────────────────────────┘
```

---

## 🗄️ Database Schema (9 Tables)

```
users  ──────────────────────────────────────────┐
  └─── cases ──────────────────────────────────┐ │
         ├─── clinical_data                    │ │
         ├─── analysis_results                 │ │
         │      └─── treatment_pathways        │ │
         ├─── reports ────────────────────────┐│ │
         ├─── pdf_exports                     ││ │
         ├─── notifications                   ││ │
         └─── second_opinions                 ││ │
                                              ││ │
audit_logs ──────────────────────────────────┘┘ │
  (every write referenced back to users) ────────┘
```

---

## 🌐 API Reference

Base URL: `http://localhost:8000`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Login, returns JWT pair |
| `POST` | `/api/auth/refresh` | Refresh access token |
| `GET`  | `/api/cases` | List all cases for authenticated doctor |
| `POST` | `/api/cases` | Create new patient case |
| `GET`  | `/api/cases/{id}/clinical` | Retrieve clinical data |
| `POST` | `/api/cases/{id}/clinical` | Submit biomarker data |
| `POST` | `/api/cases/{id}/analyse` | **Run 5-stage clinical engine** |
| `POST` | `/api/cases/{id}/simulate` | Run simulation (what-if) |
| `POST` | `/api/cases/{id}/reports` | Upload lab report (NLP extraction) |
| `GET`  | `/api/cases/{id}/export/pdf` | Generate & upload signed PDF |
| `GET`  | `/api/analytics` | Aggregate analytics dashboard data |
| `GET`  | `/api/notifications` | Fetch doctor notifications |
| `POST` | `/api/second-opinion` | Request second-opinion workflow |
| `GET`  | `/health` | Health check |

> Full interactive documentation: [`/docs`](http://localhost:8000/docs) (Swagger UI)

---

## 🗺️ Roadmap

- [x] 5-stage biomarker clinical engine
- [x] NLP extraction from uploaded PDFs/DOCX
- [x] Signed PDF export with WeasyPrint
- [x] JWT auth with refresh tokens + audit logging
- [x] 50-case dev seed + dataset validation endpoint
- [ ] DICOM image viewer integration
- [ ] Multi-institution second-opinion network
- [ ] FHIR R4 export compatibility
- [ ] Mobile companion app (React Native)

---

## 🤝 Contributing

1. Fork the repo and create your feature branch: `git checkout -b feat/amazing-feature`
2. Follow the existing code conventions (ESLint / Black)
3. Write tests for any new engine logic
4. Open a pull request — all PRs trigger the test suite automatically

---

## 📜 License

This project is licensed under the **MIT License**. See [`LICENSE`](./LICENSE) for details.

---

<p align="center">
  Made with ❤️ as a capstone project · 2026<br/>
  <em>"Precision medicine, one biomarker at a time."</em>
</p>
