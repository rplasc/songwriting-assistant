from fastapi.testclient import TestClient

from app.core.config import settings


def test_evaluation_endpoint_happy_path(client: TestClient) -> None:
    resp = client.post(
        "/v1/evaluation/regression-report",
        json={"kinds": ["rhyme"], "include_cases": False},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["contract_version"] == "phase-5.5.m3"
    assert "rhyme" in body["by_kind"]
    assert body["totals"]["cases"] > 0
    assert body["cases"] is None


def test_evaluation_endpoint_include_cases_returns_per_case(client: TestClient) -> None:
    resp = client.post(
        "/v1/evaluation/regression-report",
        json={"kinds": ["draft_compare"], "include_cases": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["cases"]
    assert all("kind" in c and "elapsed_ms" in c for c in body["cases"])


def test_evaluation_endpoint_returns_404_when_disabled(client: TestClient) -> None:
    original = settings.expose_evaluation_endpoint
    settings.expose_evaluation_endpoint = False
    try:
        resp = client.post(
            "/v1/evaluation/regression-report",
            json={"kinds": ["rhyme"]},
        )
        assert resp.status_code == 404
    finally:
        settings.expose_evaluation_endpoint = original
