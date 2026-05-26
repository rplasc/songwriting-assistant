from fastapi.testclient import TestClient

from app.services.evaluation_report_service import EvaluationReportService


def _service(client: TestClient) -> EvaluationReportService:
    return client.app.state.evaluation_report_service


def test_report_shape_for_rhyme_kind(client: TestClient) -> None:
    report = _service(client).generate(kinds=["rhyme"])
    assert report.totals.cases > 0
    assert (
        report.totals.passed + report.totals.failed + report.totals.skipped
        == report.totals.cases
    )
    assert "rhyme" in report.by_kind
    stats = report.by_kind["rhyme"]
    assert stats.passed + stats.failed == stats.cases
    assert stats.max_ms >= stats.p95_ms >= stats.p50_ms >= 0.0


def test_include_cases_false_strips_per_case_results(client: TestClient) -> None:
    report = _service(client).generate(kinds=["draft_compare"], include_cases=False)
    assert report.cases is None


def test_include_cases_true_returns_per_case_results(client: TestClient) -> None:
    report = _service(client).generate(kinds=["draft_compare"], include_cases=True)
    assert report.cases is not None
    assert len(report.cases) == report.totals.cases


def test_language_filter_limits_languages(client: TestClient) -> None:
    report = _service(client).generate(
        kinds=["draft_compare"], languages=["es"], include_cases=True
    )
    assert report.cases
    assert all(c.language == "es" for c in report.cases)


def test_contract_version_is_phase_5_5_m3(client: TestClient) -> None:
    report = _service(client).generate(kinds=["rhyme"])
    assert report.contract_version == "phase-5.5.m3"
