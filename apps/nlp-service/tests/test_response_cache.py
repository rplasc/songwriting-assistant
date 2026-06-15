import asyncio

import pytest

from app.api.routes import analysis as analysis_route
from app.api.routes import rhymes as rhymes_route
from app.schemas.draft_analysis import DraftAnalysisRequest
from app.services.response_cache import ResponseCache


def _run(coro):
    return asyncio.run(coro)


def test_disabled_cache_returns_none_and_swallows_set():
    cache = ResponseCache.disabled()
    assert cache.enabled is False
    assert _run(cache.get("anything")) is None
    _run(cache.set("anything", {"x": 1}))  # no raise


def test_make_key_is_stable_for_equivalent_payloads():
    a = DraftAnalysisRequest(language="en", content="hello world", title="t")
    b = DraftAnalysisRequest(title="t", content="hello world", language="en")
    key_a = ResponseCache.make_key("ns", a)
    key_b = ResponseCache.make_key("ns", b)
    assert key_a == key_b
    assert key_a.startswith("ns:")


def test_make_key_differs_for_different_payloads():
    a = DraftAnalysisRequest(language="en", content="hello world")
    b = DraftAnalysisRequest(language="en", content="hello world!")
    assert ResponseCache.make_key("ns", a) != ResponseCache.make_key("ns", b)


class _BoomClient:
    async def get(self, key):
        raise ConnectionError("redis down")

    async def set(self, key, value, ex=None):
        raise ConnectionError("redis down")

    async def aclose(self):
        pass


def test_cache_errors_are_swallowed():
    cache = ResponseCache(client=_BoomClient(), ttl_seconds=60)
    assert cache.enabled is True
    assert _run(cache.get("k")) is None
    _run(cache.set("k", {"v": 1}))  # no raise


class _FakeClient:
    def __init__(self):
        self.store: dict[str, bytes] = {}
        self.get_calls = 0
        self.set_calls = 0

    async def get(self, key):
        self.get_calls += 1
        return self.store.get(key)

    async def set(self, key, value, ex=None):
        self.set_calls += 1
        self.store[key] = value

    async def aclose(self):
        pass


_DRAFT_PAYLOAD = {
    "language": "en",
    "content": (
        "I hear your shadow in the hall\n"
        "I hear your footsteps on the floor\n"
        "\n"
        "[chorus]\n"
        "Hold me in the midnight window\n"
        "Hold me when the city glows"
    ),
}


@pytest.fixture
def cached_client(client):
    fake = _FakeClient()
    prior = client.app.state.response_cache
    client.app.state.response_cache = ResponseCache(client=fake, ttl_seconds=60)
    try:
        yield client, fake
    finally:
        client.app.state.response_cache = prior


def test_analyze_draft_cache_hit_skips_service(cached_client, monkeypatch):
    tc, fake = cached_client

    service = tc.app.state.draft_analysis_service
    real_analyze = service.analyze
    calls = {"n": 0}

    def counting_analyze(payload, ctx):
        calls["n"] += 1
        return real_analyze(payload, ctx)

    monkeypatch.setattr(service, "analyze", counting_analyze)

    r1 = tc.post("/v1/analyze-draft", json=_DRAFT_PAYLOAD)
    assert r1.status_code == 200
    assert calls["n"] == 1
    assert fake.set_calls == 1
    assert len(fake.store) == 1

    r2 = tc.post("/v1/analyze-draft", json=_DRAFT_PAYLOAD)
    assert r2.status_code == 200
    assert calls["n"] == 1, "service should NOT be invoked on cache hit"
    assert r2.json() == r1.json()


@pytest.fixture
def cached_rhyme_client(client):
    fake = _FakeClient()
    prior = client.app.state.rhyme_response_cache
    client.app.state.rhyme_response_cache = ResponseCache(client=fake, ttl_seconds=60)
    try:
        yield client, fake
    finally:
        client.app.state.rhyme_response_cache = prior


def test_rhymes_cache_hit_skips_compute(cached_rhyme_client, monkeypatch):
    tc, fake = cached_rhyme_client

    real_compute = rhymes_route._compute_rhymes
    calls = {"n": 0}

    def counting_compute(payload, ctx):
        calls["n"] += 1
        return real_compute(payload, ctx)

    monkeypatch.setattr(rhymes_route, "_compute_rhymes", counting_compute)

    r1 = tc.post("/v1/rhymes", json={"word": "fire", "limit": 5})
    assert r1.status_code == 200
    assert calls["n"] == 1
    assert fake.set_calls == 1
    assert len(fake.store) == 1

    r2 = tc.post("/v1/rhymes", json={"word": "fire", "limit": 5})
    assert r2.status_code == 200
    assert calls["n"] == 1, "second request should be served from cache"
    assert r2.json() == r1.json()


def test_analyze_line_cache_hit_skips_compute(cached_rhyme_client, monkeypatch):
    tc, fake = cached_rhyme_client

    real_compute = analysis_route._compute_analyze_line
    calls = {"n": 0}

    def counting_compute(payload, ctx):
        calls["n"] += 1
        return real_compute(payload, ctx)

    monkeypatch.setattr(analysis_route, "_compute_analyze_line", counting_compute)

    payload = {"language": "en", "line": "I hear your shadow in the hall"}
    r1 = tc.post("/v1/analyze-line", json=payload)
    assert r1.status_code == 200
    assert calls["n"] == 1
    assert fake.set_calls == 1

    r2 = tc.post("/v1/analyze-line", json=payload)
    assert r2.status_code == 200
    assert calls["n"] == 1, "second request should be served from cache"
    assert r2.json() == r1.json()


def test_analyze_draft_compare_cache_hit_skips_service(cached_client, monkeypatch):
    tc, fake = cached_client

    service = tc.app.state.draft_compare_service
    real_compare = service.compare
    calls = {"n": 0}

    def counting_compare(payload, ctx):
        calls["n"] += 1
        return real_compare(payload, ctx)

    monkeypatch.setattr(service, "compare", counting_compare)

    payload = {
        "language": "en",
        "previous": {"content": "I walk alone tonight\nI hold my dreams in sight"},
        "current": {"content": "I walk alone tonight\nI watch the stars ignite"},
    }
    r1 = tc.post("/v1/analyze-draft-compare", json=payload)
    assert r1.status_code == 200
    assert calls["n"] == 1

    r2 = tc.post("/v1/analyze-draft-compare", json=payload)
    assert r2.status_code == 200
    assert calls["n"] == 1
    assert r2.json() == r1.json()
