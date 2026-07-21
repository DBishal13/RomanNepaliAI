from roman_nepali_ai.transliterate import roman_to_devanagari


def test_stub_transliteration_returns_input():
    # The transliteration function is a stub; it should currently return the input unchanged.
    assert roman_to_devanagari("namaste") == "namaste"
