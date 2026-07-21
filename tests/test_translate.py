from roman_nepali_ai.translate import Translator


def test_stub_translate_returns_input():
    t = Translator(backend='stub')
    assert t.translate('मेरो नाम') == 'मेरो नाम'
