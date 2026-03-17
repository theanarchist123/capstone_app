"""
tests/conftest.py — Shared pytest fixtures.
Uses an in-memory SQLite database for fast, isolated tests.
"""
import asyncio
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from core.database import Base, get_db
from core.security import hash_password, create_access_token
from main import app
from models.user import User
from models.case import Case
from models.clinical_data import ClinicalData

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    AsyncTestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncTestSession() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_doctor(db_session) -> User:
    user = User(
        name="Dr. Test Oncologist",
        email=f"doctor_{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("TestPass123"),
        role="doctor",
        hospital="Test Medical Centre",
        designation="Consultant Oncologist",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_doctor) -> dict:
    token = create_access_token(str(test_doctor.id), test_doctor.role)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def sample_case(db_session, test_doctor) -> Case:
    case = Case(doctor_id=test_doctor.id, patient_name="Jane Doe", patient_age=52, status="draft")
    db_session.add(case)
    await db_session.commit()
    await db_session.refresh(case)
    return case


@pytest_asyncio.fixture
async def sample_clinical(db_session, sample_case) -> ClinicalData:
    cd = ClinicalData(
        case_id=sample_case.id,
        er_status="Positive", pr_status="Positive", her2_status="Negative",
        ki67_percent=10.0, stage="II", grade=2,
        tumour_size=2.3, lymph_nodes_involved=False,
        menopausal_status="Post-menopausal", ecog_score=0,
        lvef_percent=62.0, brca1_status="Negative", brca2_status="Negative",
    )
    db_session.add(cd)
    await db_session.commit()
    await db_session.refresh(cd)
    return cd
