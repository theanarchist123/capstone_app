
<p align="center">
  <img src="https://readme-typing-svg.demolab.com?font=Outfit&weight=700&size=36&duration=3000&pause=800&color=E84A5F&center=true&vCenter=true&width=600&lines=OnCopilot+Backend;FastAPI+·+Python+·+Clinical+AI" alt="Typing SVG" />
</p>

<p align="center">
  <strong>Async clinical decision-support API for oncology</strong><br/>
  5-stage biomarker engine · NLP extraction · PDF generation · JWT auth
</p>

<p align="center">
  <img src="https://skillicons.dev/icons?i=python,fastapi,postgres,supabase,pytest" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0_async-D71F00?style=flat-square" />
  <img src="https://img.shields.io/badge/Pydantic-v2-E92063?style=flat-square&logo=pydantic&logoColor=white" />
  <img src="https://img.shields.io/badge/spaCy-NLP-09A3D5?style=flat-square" />
</p>

---

## 🧠 Clinical Engine — 5-Stage Pipeline

```
  Patient Biomarkers
         │
         ▼
  ┌─────────────────────────────────────────────────┐
  │  Stage 1 · Subtype Classification               │
  │  ER/PR/HER2/Ki-67 → Luminal A/B, HER2+, TNBC   │
  └───────────────────────┬─────────────────────────┘
                          │
                          ▼
  ┌─────────────────────────────────────────────────┐
  │  Stage 2 · Genomic Risk Modifiers               │
  │  OncotypeDX · MammaPrint · BRCA1/2              │
  └───────────────────────┬─────────────────────────┘
                          │
                          ▼
  ┌─────────────────────────────────────────────────┐
  │  Stage 3 · Immune & Mutation Flags              │
  │  PD-L1 · TILs · PIK3CA · TP53 · TOP2A          │
  └───────────────────────┬─────────────────────────┘
                          │
                          ▼
  ┌─────────────────────────────────────────────────┐
  │  Stage 4 · Treatment Pathway Generation         │
  │  2–4 ranked protocols + rule trace              │
  └───────────────────────┬─────────────────────────┘
                          │
                          ▼
  ┌─────────────────────────────────────────────────┐
  │  Stage 5 · Contraindication Safety Check        │
  │  Cardiac · Renal · Hepatic · ECOG · Allergies   │
  └───────────────────────┬─────────────────────────┘
                          │
                          ▼
            Ranked Treatment Recommendations
```

| # | Function | Criteria |
|---|----------|----------|
| 1 | `classify_subtype()` | NCCN / St.Gallen molecular subtyping |
| 2 | `genomic_risk_modifiers()` | Adjust risk tier from genomic assay scores |
| 3 | `immune_mutation_flags()` | Eligibility flags for immunotherapy & targeted agents |
| 4 | `generate_treatment_pathways()` | AC→T, CDK4/6 + ET, trastuzumab combos, etc. |
| 5 | `check_contraindications()` | 6 safety rules, blocks unsafe protocols |

---

## 📁 Project Structure

```
backend/
├── main.py                        ← FastAPI app + all router mounts
│
├── core/
│   ├── config.py                  ← Pydantic settings from .env
│   ├── security.py                ← JWT encode/decode + bcrypt
│   └── database.py                ← Async SQLAlchemy engine & session
│
├── api/
│   ├── deps.py                    ← get_current_user + role_required
│   └── routes/
│       ├── auth.py                ← POST /api/auth/login|refresh|logout
│       ├── cases.py               ← GET|POST /api/cases
│       ├── clinical.py            ← /api/cases/{id}/clinical
│       ├── analysis.py            ← /api/cases/{id}/analyse|simulate
│       ├── reports.py             ← /api/cases/{id}/reports (NLP upload)
│       ├── pdf.py                 ← /api/cases/{id}/export/pdf
│       ├── analytics.py           ← /api/analytics
│       ├── notifications.py       ← /api/notifications
│       └── second_opinion.py      ← /api/second-opinion
│
├── engine/
│   ├── biomarker_algorithm.py     ← ⭐ 5-stage clinical pipeline
│   ├── contraindication_checker.py ← 6 safety rules
│   └── nlp_extractor.py           ← spaCy: 13 entity types
│
├── services/
│   ├── case_service.py            ← CRUD + audit log writes
│   ├── report_service.py          ← Supabase upload + background NLP
│   └── pdf_service.py             ← WeasyPrint HTML→PDF
│
├── models/                        ← SQLAlchemy ORM (9 tables)
├── schemas/                       ← Pydantic v2 request/response
├── alembic/                       ← Async migration scripts
├── scripts/seed.py                ← 50 anonymised dev cases
└── tests/
    ├── conftest.py                 ← SQLite in-memory fixtures
    ├── test_engine.py              ← Engine unit tests (all 5 stages)
    ├── test_auth.py                ← Auth flow + token tests
    └── test_cases.py              ← CRUD + analysis integration
```

---

## ⚡ Setup

### 1. Create virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt

# Download spaCy English language model
python -m spacy download en_core_web_sm
```

### 3. Configure environment

```bash
copy .env.example .env    # Windows
cp .env.example .env      # macOS / Linux
```

Edit `.env`:

```env
APP_ENV=development
DEBUG=true
SECRET_KEY=your-super-secret-jwt-key-min-32-chars

SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-role-key
SUPABASE_BUCKET=reports

DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname

ORIGINS=http://localhost:3002
RATE_LIMIT_PER_MINUTE=60
```

### 4. Run migrations & seed

```bash
alembic upgrade head
python scripts/seed.py
# Dev login → seed.doctor@oncopilot.dev
```

### 5. Start server

```bash
uvicorn main:app --reload --port 8000
```

| Endpoint | URL |
|----------|-----|
| 🟢 API | `http://localhost:8000` |
| 📖 Swagger UI | `http://localhost:8000/docs` |
| 📘 ReDoc | `http://localhost:8000/redoc` |
| 💓 Health | `http://localhost:8000/health` |

---

## 🧪 Running Tests

```bash
pip install aiosqlite    # required for in-memory test DB

pytest --cov=. --cov-report=term-missing
```

| Test File | What it covers |
|-----------|---------------|
| `test_engine.py` | All 5 pipeline stages, edge cases |
| `test_auth.py` | Login, token refresh, role guards |
| `test_cases.py` | Case CRUD + full analysis integration |

---

## 🗄️ Database (9 Tables)

| Table | Description |
|-------|-------------|
| `users` | Doctor accounts (bcrypt password, role) |
| `cases` | Patient cases linked to a doctor |
| `clinical_data` | Biomarker inputs per case |
| `analysis_results` | Engine outputs, rule traces |
| `treatment_pathways` | Ranked treatment options |
| `reports` | Uploaded file metadata + NLP entities |
| `pdf_exports` | Generated PDF references (signed URL) |
| `notifications` | Doctor notification feed |
| `audit_logs` | Every DB write, timestamped |

---

## 🔐 Security

| Control | Detail |
|---------|--------|
| Access token lifespan | **15 minutes** |
| Refresh token lifespan | **7 days** |
| Password hashing | **bcrypt** |
| Patient data scope | Doctors access **own cases only** |
| File uploads | PDF / DOCX / TXT · Max **10 MB** |
| Storage | Supabase **private bucket** with signed URLs |
| Rate limiting | **slowapi** per-IP, configurable RPM |
| Audit trail | Every write logged to `audit_logs` |

---

## 📊 API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| `POST` | `/api/auth/login` | Authenticate, receive JWT pair |
| `POST` | `/api/auth/refresh` | Rotate access token |
| `GET` | `/api/cases` | List doctor's cases |
| `POST` | `/api/cases` | Create patient case |
| `POST` | `/api/cases/{id}/clinical` | Submit biomarker data |
| `POST` | `/api/cases/{id}/analyse` | **Run clinical engine** ⭐ |
| `POST` | `/api/cases/{id}/simulate` | What-if simulation |
| `POST` | `/api/cases/{id}/reports` | Upload + NLP-extract report |
| `GET` | `/api/cases/{id}/export/pdf` | Generate signed PDF |
| `GET` | `/api/analytics` | Aggregate analytics |
| `GET` | `/api/notifications` | Doctor notification feed |

---

<p align="center">
  <em>Clinical intelligence, engineered with care. 🩺</em>
</p>
