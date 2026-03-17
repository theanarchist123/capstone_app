# OnCopilot Backend

Clinical decision-support backend for oncology.

## Stack
- **FastAPI** + **Pydantic v2** — async REST API
- **PostgreSQL** via **Supabase** + **SQLAlchemy 2.0 async**
- **Alembic** — database migrations
- **JWT** (python-jose) + **bcrypt** — authentication
- **spaCy** — NLP report extraction
- **WeasyPrint** — PDF generation
- **Supabase Storage** — file uploads (private bucket, signed URLs)
- **Pytest + httpx** — test suite

## Setup

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Install spaCy English model
python -m spacy download en_core_web_sm

# Configure environment
copy .env.example .env
# Edit .env with your Supabase credentials and secret key

# Run database migrations
alembic upgrade head

# Seed development database (50 anonymised cases)
python scripts/seed.py   # seeds 50 dev cases with login seed.doctor@oncopilot.dev
# Start development server
uvicorn main:app --reload --port 8000
```

## API Docs
Visit `http://localhost:8000/docs` for the interactive API explorer

## Project Structure

```
oncopilot-backend/
├── main.py                    # FastAPI app + router registration
├── core/
│   ├── config.py              # Settings from .env
│   ├── security.py            # JWT + bcrypt
│   └── database.py            # Async SQLAlchemy engine
├── models/                    # SQLAlchemy models (9 tables)
├── schemas/                   # Pydantic v2 request/response schemas
├── api/
│   ├── deps.py                # JWT auth dependency + role guard
│   └── routes/                # 9 route files
│       ├── auth.py            # /api/auth/*
│       ├── cases.py           # /api/cases/*
│       ├── clinical.py        # /api/cases/{id}/clinical/*
│       ├── analysis.py        # /api/cases/{id}/analyse + /simulate
│       ├── reports.py         # /api/cases/{id}/reports/*
│       ├── pdf.py             # /api/cases/{id}/export/pdf
│       ├── analytics.py       # /api/analytics/*
│       ├── notifications.py   # /api/notifications/*
│       └── second_opinion.py  # /api/second-opinion/*
├── engine/
│   ├── biomarker_algorithm.py # 5-stage clinical pipeline (core)
│   ├── contraindication_checker.py # 6 safety rules
│   └── nlp_extractor.py       # spaCy NLP for 13 clinical entities
├── services/
│   ├── case_service.py        # Case CRUD + audit logging
│   ├── report_service.py      # Supabase upload + NLP background task
│   └── pdf_service.py         # WeasyPrint PDF generation
├── scripts/
│   └── seed.py                # 50 anonymised dev cases
├── tests/
│   ├── conftest.py            # SQLite test fixtures
│   ├── test_engine.py         # Engine unit tests (all 5 stages)
│   ├── test_auth.py           # Auth flow tests
│   └── test_cases.py          # Case CRUD + analysis integration tests
├── alembic/                   # Async migrations
├── data/                      # Place breast_cancer_dataset.csv here
├── requirements.txt
└── .env.example
```

## Running Tests

```bash
pip install aiosqlite          # Required for in-memory test DB
pytest --cov=. --cov-report=term-missing
```

## Clinical Engine Overview

The 5-stage pipeline in `engine/biomarker_algorithm.py`:

| Stage | Module | Description |
|-------|--------|-------------|
| 1 | `classify_subtype()` | NCCN/St.Gallen subtype from ER/PR/HER2/Ki-67 |
| 2 | `genomic_risk_modifiers()` | OncotypeDX, MammaPrint, BRCA |
| 3 | `immune_mutation_flags()` | PD-L1, TILs, PIK3CA, TP53, TOP2A, BCL2, Cyclin-D1 |
| 4 | `generate_treatment_pathways()` | 2-4 ranked protocols with rule trace |
| 5 | `check_contraindications()` | Cardiac, ECOG, Renal, Hepatic, Allergy |

## Dataset Validation

Place `data/breast_cancer_dataset.csv` in the project root.
Visit `GET /api/dev/dataset-stats` to see classifier accuracy metrics.

## Security

- Access tokens: **15-minute** expiry
- Refresh tokens: **7-day** expiry  
- All patient data requires verified JWT
- Doctors can only access their own cases
- Every DB write is logged to `audit_logs`
- File uploads: PDF/DOCX/TXT only, max 10 MB, Supabase private bucket with signed URLs
