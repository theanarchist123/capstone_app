"""
services/report_service.py
Handles file upload to Supabase Storage,
NLP extraction background task, and DB persistence.
"""
from __future__ import annotations

import io
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.config import settings
from models.report import Report
from engine.nlp_extractor import extract_from_text, map_to_clinical_fields

try:
    from supabase import create_client, Client
    _supabase: Client = create_client(settings.supabase_url, settings.supabase_key)
except Exception:
    _supabase = None  # type: ignore


ALLOWED_MIME = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
}
MAX_BYTES = 10 * 1024 * 1024  # 10 MB


async def upload_report(
    db: AsyncSession,
    case_id: uuid.UUID,
    filename: str,
    content: bytes,
    content_type: str,
) -> Report:
    if content_type not in ALLOWED_MIME:
        raise ValueError(f"Unsupported file type: {content_type}. Allowed: PDF, DOCX, TXT")
    if len(content) > MAX_BYTES:
        raise ValueError("File exceeds 10 MB limit")

    ext = ALLOWED_MIME[content_type]
    storage_path = f"{case_id}/{uuid.uuid4()}.{ext}"

    # Upload to Supabase private bucket
    file_url = storage_path
    if _supabase:
        try:
            _supabase.storage.from_(settings.supabase_bucket).upload(
                storage_path, content, {"content-type": content_type, "upsert": "false"}
            )
            # Signed URL (valid 1 hour)
            signed = _supabase.storage.from_(settings.supabase_bucket).create_signed_url(storage_path, 3600)
            file_url = signed.get("signedURL", storage_path)
        except Exception as e:
            raise RuntimeError(f"Supabase upload failed: {e}") from e

    report = Report(
        case_id=case_id,
        file_name=filename,
        file_url=file_url,
        file_type=ext,
        extraction_confidence=0.0,
        verified_by_doctor=False,
    )
    db.add(report)
    await db.flush()
    return report


async def run_nlp_extraction(db: AsyncSession, report_id: uuid.UUID, text: str) -> None:
    """Called as a background task after upload."""
    q = select(Report).where(Report.id == report_id)
    r = await db.execute(q)
    report = r.scalar_one_or_none()
    if not report:
        return

    result = extract_from_text(text)
    report.extracted_raw = result["extracted"]
    report.extraction_confidence = result["overall_confidence"]
    await db.commit()


async def get_signed_url(storage_path: str, expires: int = 3600) -> str:
    if _supabase:
        signed = _supabase.storage.from_(settings.supabase_bucket).create_signed_url(storage_path, expires)
        return signed.get("signedURL", storage_path)
    return storage_path
