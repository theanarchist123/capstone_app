"""
scripts/seed.py
Seed dev database with 50 anonymised breast cancer patient cases.
Run: python scripts/seed.py
"""
import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

import sys
from pathlib import Path

# Fix python path so it can find the 'core' and 'models' modules
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from core.config import settings
from core.database import Base
from core.security import hash_password
from models.user import User
from models.case import Case
from models.clinical_data import ClinicalData
from models.result import Result
from engine.biomarker_algorithm import ClinicalInput, run_pipeline

import models  # ensure all tables registered


engine = create_async_engine(
    settings.database_url, 
    echo=False,
    connect_args={
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0,
    },
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ─── Realistic distributions ──────────────────────────────────────────────────
SUBTYPES = [
    # (er, pr, her2, ki67_range)
    ("Positive", "Positive", "Negative", (5, 13)),     # Luminal A
    ("Positive", "Positive", "Negative", (15, 40)),    # Luminal B HER2-
    ("Positive", "Positive", "Positive", (15, 50)),    # Luminal B HER2+
    ("Negative", "Negative", "Positive", (30, 70)),    # HER2-Enriched
    ("Negative", "Negative", "Negative", (40, 90)),    # Triple-Negative
]

STAGES = ["I", "IIA", "IIB", "IIIA", "IIIB", "IV"]
GRADES = [1, 2, 3]
MENO = ["Pre-menopausal", "Post-menopausal", "Peri-menopausal"]
HISTOLOGY = ["Invasive Ductal Carcinoma", "Invasive Lobular Carcinoma", "Mixed Ductal-Lobular", "Mucinous Carcinoma"]
NAMES = [
    "Priya Sharma", "Anita Rao", "Meena Patel", "Sunita Gupta", "Rekha Nair",
    "Deepa Kumar", "Kavita Singh", "Sudha Reddy", "Usha Mehta", "Aruna Das",
    "Leela Iyer", "Geeta Joshi", "Sujata Pillai", "Mala Bose", "Renuka Shah",
    "Kaveri Thakur", "Indira Mishra", "Lalitha Menon", "Nandita Roy", "Parvati Sinha",
    "Rama Iyengar", "Shanti Desai", "Vidya Pandey", "Hema Verma", "Suman Khanna",
    "Sudha Iyer", "Kalpana Tiwari", "Sarla Bhatt", "Pushpa Choudhury", "Maya Agarwal",
    "Sushila Rao", "Vandana Nair", "Chitra Kumar", "Radha Singh", "Laxmi Reddy",
    "Savitri Jain", "Usha Pillai", "Manju Shah", "Prema Thakur", "Nirmala Mishra",
    "Padma Menon", "Rohini Desai", "Swati Pandey", "Tara Verma", "Asha Khanna",
    "Nalini Iyer", "Kamala Tiwari", "Durga Bhatt", "Saraswati Choudhury", "Mythili Agarwal",
]


def _rand_status(positive_prob: float = 0.5) -> str:
    return "Positive" if random.random() < positive_prob else "Negative"


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Create seed doctor
        doctor_email = "seed.doctor@oncopilot.dev"
        from sqlalchemy import select
        existing = (await db.execute(select(User).where(User.email == doctor_email))).scalar_one_or_none()
        if not existing:
            doctor = User(
                name="Dr. Seed Oncologist",
                email=doctor_email,
                password_hash=hash_password("SeedPass123!"),
                role="doctor",
                hospital="AIIMS Delhi (Demo)",
                designation="Sr. Medical Oncologist",
                license_number="OCP-DEMO-001",
            )
            db.add(doctor)
            await db.flush()
        else:
            doctor = existing

        created = 0
        for i in range(50):
            er, pr, her2, ki67_range = random.choice(SUBTYPES)
            ki67 = round(random.uniform(*ki67_range), 1)
            age = random.randint(32, 72)
            days_ago = random.randint(1, 365)
            created_ts = datetime.now(timezone.utc) - timedelta(days=days_ago)

            case = Case(
                doctor_id=doctor.id,
                patient_name=NAMES[i],
                patient_age=age,
                status=random.choice(["draft", "under_analysis", "treatment_decided"]),
                tags=[random.choice(["urgent", "follow-up", "MDT", "research"])],
                created_at=created_ts,
                updated_at=created_ts,
            )
            db.add(case)
            await db.flush()

            lvef = round(random.uniform(45, 75), 1)
            cd = ClinicalData(
                case_id=case.id,
                er_status=er, pr_status=pr, her2_status=her2, ki67_percent=ki67,
                stage=random.choice(STAGES),
                grade=random.choice(GRADES),
                tumour_size=round(random.uniform(0.8, 5.0), 1),
                histological_type=random.choice(HISTOLOGY),
                lymph_nodes_involved=random.random() > 0.5,
                lymph_node_count=random.randint(0, 10),
                menopausal_status=random.choice(MENO),
                ecog_score=random.choice([0, 0, 0, 1, 1, 2]),
                lvef_percent=lvef,
                brca1_status=_rand_status(0.1),
                brca2_status=_rand_status(0.1),
                pdl1_status=_rand_status(0.25),
                pik3ca_status=_rand_status(0.3),
                tp53_status=_rand_status(0.35),
                tils_percent=round(random.uniform(0, 60), 1),
                oncotype_dx_score=round(random.uniform(5, 45), 0) if er == "Positive" and her2 == "Negative" else None,
            )
            db.add(cd)
            await db.flush()

            # Run engine and save result
            ci = ClinicalInput(
                er_status=er, pr_status=pr, her2_status=her2, ki67_percent=ki67,
                stage=cd.stage or "II", grade=cd.grade or 2,
                lymph_nodes_involved=cd.lymph_nodes_involved or False,
                menopausal_status=cd.menopausal_status or "Unknown",
                ecog_score=cd.ecog_score or 0,
                lvef_percent=lvef,
                brca1_status=cd.brca1_status or "Unknown",
                brca2_status=cd.brca2_status or "Unknown",
                pdl1_status=cd.pdl1_status or "Unknown",
                oncotype_dx_score=cd.oncotype_dx_score,
            )
            pr_result = run_pipeline(ci)
            result = Result(
                case_id=case.id,
                version=1,
                molecular_subtype=pr_result.molecular_subtype,
                subtype_confidence=pr_result.subtype_confidence,
                recommendations=pr_result.recommendations,
                alerts=pr_result.alerts,
                rule_trace=pr_result.rule_trace,
                is_simulation=False,
                created_at=created_ts,
            )
            db.add(result)
            created += 1

        await db.commit()
        print(f"✅ Seeded {created} cases for {doctor.email}")
        print("   Login: seed.doctor@oncopilot.dev / SeedPass123!")


if __name__ == "__main__":
    asyncio.run(seed())
