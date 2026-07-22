import pytest
from unittest.mock import MagicMock

from roman_nepali_ai.translate import Translator, translate_text


def test_stub_translate_returns_input():
    t = Translator(backend='stub')
    assert t.translate('मेरो नाम') == 'मेरो नाम'


def test_stub_translate_is_direction_agnostic():
    t = Translator(backend='stub')
    assert t.translate('hello', src='en', tgt='ne') == 'hello'


def test_translate_text_convenience_passes_direction():
    assert translate_text('hello', backend='stub', src='en', tgt='ne') == 'hello'


def test_hf_rejects_non_ne_en_direction(monkeypatch):
    transformers = pytest.importorskip("transformers")
    monkeypatch.setattr(transformers.MarianTokenizer, "from_pretrained", lambda name: MagicMock())
    monkeypatch.setattr(transformers.MarianMTModel, "from_pretrained", lambda name: MagicMock())

    t = Translator(backend='hf')
    assert t.available

    with pytest.raises(RuntimeError, match="ne.*en"):
        t.translate('hello', src='en', tgt='ne')


def test_google_backend_passes_src_tgt_through():
    pytest.importorskip("deep_translator")
    t = Translator(backend='google')
    assert t.available

    calls = []

    class FakeGoogleTranslator:
        def __init__(self, source, target):
            calls.append((source, target))

        def translate(self, text):
            return f"[{text}]"

    t._google_translator_cls = FakeGoogleTranslator

    assert t.translate('hello', src='en', tgt='ne') == '[hello]'
    assert calls[-1] == ('en', 'ne')

    assert t.translate('namaste', src='ne', tgt='en') == '[namaste]'
    assert calls[-1] == ('ne', 'en')
