import pytest

fastapi_testclient = pytest.importorskip("fastapi.testclient")
TestClient = fastapi_testclient.TestClient

from roman_nepali_ai import server as server_module

client = TestClient(server_module.app)


@pytest.fixture(autouse=True)
def clear_translator_cache():
    # _translators is a module-level cache that persists across requests
    # (and would otherwise leak a stale/fake Translator between tests).
    server_module._translators.clear()
    yield
    server_module._translators.clear()


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_translate_empty_text_short_circuits(monkeypatch):
    called = False

    class ShouldNotBeCalled:
        def __init__(self, backend, model_name=None):
            nonlocal called
            called = True

    monkeypatch.setattr(server_module, "Translator", ShouldNotBeCalled)

    res = client.post("/translate", json={"text": "   ", "backend": "stub"})
    assert res.status_code == 200
    assert res.json() == {"translation": "", "error": False}
    assert called is False


def test_translate_passes_src_tgt_through(monkeypatch):
    calls = []

    class FakeTranslator:
        def __init__(self, backend, model_name=None):
            self.backend = backend

        def translate(self, text, src="ne", tgt="en"):
            calls.append((text, src, tgt))
            return f"[{text}:{src}->{tgt}]"

    monkeypatch.setattr(server_module, "Translator", FakeTranslator)

    res = client.post("/translate", json={"text": "My name is Bishal", "backend": "google", "src": "en", "tgt": "ne"})
    assert res.status_code == 200
    body = res.json()
    assert body["error"] is False
    assert body["translation"] == "[My name is Bishal:en->ne]"
    assert calls == [("My name is Bishal", "en", "ne")]


def test_translate_defaults_to_ne_en(monkeypatch):
    calls = []

    class FakeTranslator:
        def __init__(self, backend, model_name=None):
            pass

        def translate(self, text, src="ne", tgt="en"):
            calls.append((src, tgt))
            return "ok"

    monkeypatch.setattr(server_module, "Translator", FakeTranslator)

    res = client.post("/translate", json={"text": "namaste"})
    assert res.status_code == 200
    assert calls == [("ne", "en")]


def test_translate_error_path_returns_200(monkeypatch):
    class FailingTranslator:
        def __init__(self, backend, model_name=None):
            pass

        def translate(self, text, src="ne", tgt="en"):
            raise RuntimeError("boom")

    monkeypatch.setattr(server_module, "Translator", FailingTranslator)

    res = client.post("/translate", json={"text": "hello", "backend": "hf"})
    assert res.status_code == 200
    body = res.json()
    assert body["error"] is True
    assert "boom" in body["translation"]
