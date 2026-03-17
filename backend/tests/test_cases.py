"""
tests/test_cases.py
Tests for case CRUD and the analysis + simulation flow.
"""
import pytest


@pytest.mark.asyncio
async def test_create_case(client, auth_headers):
    resp = await client.post("/api/cases/", json={
        "patient_name": "Test Patient", "patient_age": 48
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["status"] == "draft"
    assert data["patient_name"] == "Test Patient"


@pytest.mark.asyncio
async def test_list_cases_empty(client, auth_headers):
    resp = await client.get("/api/cases/", headers=auth_headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_case(client, auth_headers, sample_case):
    resp = await client.get(f"/api/cases/{sample_case.id}", headers=auth_headers)
    assert resp.status_code == 200
    assert str(resp.json()["data"]["id"]) == str(sample_case.id)


@pytest.mark.asyncio
async def test_update_case_status(client, auth_headers, sample_case):
    resp = await client.patch(f"/api/cases/{sample_case.id}", json={"status": "ongoing"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "ongoing"


@pytest.mark.asyncio
async def test_delete_case(client, auth_headers, sample_case):
    resp = await client.delete(f"/api/cases/{sample_case.id}", headers=auth_headers)
    assert resp.status_code == 200
    # Verify soft-deleted (get returns 404)
    resp2 = await client.get(f"/api/cases/{sample_case.id}", headers=auth_headers)
    assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_submit_clinical_data(client, auth_headers, sample_case):
    resp = await client.post(f"/api/cases/{sample_case.id}/clinical/", json={
        "er_status": "Positive", "pr_status": "Positive",
        "her2_status": "Negative", "ki67_percent": 12.0,
        "stage": "II", "grade": 2, "lvef_percent": 65.0,
        "menopausal_status": "Post-menopausal", "ecog_score": 0,
    }, headers=auth_headers)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_run_analysis(client, auth_headers, sample_case, sample_clinical):
    resp = await client.post(f"/api/cases/{sample_case.id}/analyse", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["molecular_subtype"] == "Luminal A"
    assert data["version"] == 1
    assert isinstance(data["recommendations"], list)
    assert len(data["recommendations"]) >= 1


@pytest.mark.asyncio
async def test_simulation_returns_diff(client, auth_headers, sample_case, sample_clinical):
    # First run real analysis for a baseline
    await client.post(f"/api/cases/{sample_case.id}/analyse", headers=auth_headers)

    # Now simulate with changed her2 status
    resp = await client.post(
        f"/api/cases/{sample_case.id}/analyse/simulate",
        json={"overrides": {"her2_status": "Positive", "ki67_percent": 30.0}},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "diff_vs_baseline" in data
    # Subtype should have changed
    assert data["molecular_subtype"] != "Luminal A"


@pytest.mark.asyncio
async def test_case_history(client, auth_headers, sample_case, sample_clinical):
    await client.post(f"/api/cases/{sample_case.id}/analyse", headers=auth_headers)
    resp = await client.get(f"/api/cases/{sample_case.id}/history", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1


@pytest.mark.asyncio
async def test_analysis_without_clinical_data(client, auth_headers):
    create = await client.post("/api/cases/", json={"patient_name": "No Data"}, headers=auth_headers)
    case_id = create.json()["data"]["id"]
    resp = await client.post(f"/api/cases/{case_id}/analyse", headers=auth_headers)
    assert resp.status_code == 400
