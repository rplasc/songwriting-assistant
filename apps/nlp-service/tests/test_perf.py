import time

from fastapi.testclient import TestClient

# Loose guard: a high-candidate rhyme query should complete well inside an
# interactive-write budget. Tuned conservatively so CI variance doesn't flake.
_BUDGET_MS = 75
_WARMUP_RUNS = 2
_MEASURE_RUNS = 5


def _median_request_ms(client: TestClient, word: str) -> float:
    samples: list[float] = []
    for _ in range(_MEASURE_RUNS):
        start = time.perf_counter()
        resp = client.post("/v1/rhymes", json={"word": word, "limit": 25})
        assert resp.status_code == 200
        samples.append((time.perf_counter() - start) * 1000.0)
    samples.sort()
    return samples[len(samples) // 2]


def test_rhymes_perfect_mode_high_candidate_word(client: TestClient) -> None:
    for _ in range(_WARMUP_RUNS):
        client.post("/v1/rhymes", json={"word": "time", "limit": 25})
    median_ms = _median_request_ms(client, "time")
    assert median_ms < _BUDGET_MS, f"perfect-mode median {median_ms:.1f}ms exceeded budget"


def test_rhymes_near_mode_high_candidate_word(client: TestClient) -> None:
    for _ in range(_WARMUP_RUNS):
        client.post("/v1/rhymes", json={"word": "time", "mode": "near", "limit": 25})
    samples: list[float] = []
    for _ in range(_MEASURE_RUNS):
        start = time.perf_counter()
        resp = client.post(
            "/v1/rhymes", json={"word": "time", "mode": "near", "limit": 25}
        )
        assert resp.status_code == 200
        samples.append((time.perf_counter() - start) * 1000.0)
    samples.sort()
    median_ms = samples[len(samples) // 2]
    assert median_ms < _BUDGET_MS, f"near-mode median {median_ms:.1f}ms exceeded budget"
