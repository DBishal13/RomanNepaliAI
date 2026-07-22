from roman_nepali_ai.transliterate import roman_to_devanagari, devanagari_to_roman


def test_namaste():
    assert roman_to_devanagari("namaste") == "नमस्ते"


def test_trailing_consonant_without_vowel_gets_virama():
    # No explicit trailing vowel -> the final consonant is "dead" (virama-joined),
    # it does not implicitly carry the inherent "a".
    assert roman_to_devanagari("ghar") == "घर्"


def test_retroflex_vs_dental_is_case_sensitive():
    assert roman_to_devanagari("ta") == "त"
    assert roman_to_devanagari("Ta") == "ट"
    assert roman_to_devanagari("ta") != roman_to_devanagari("Ta")


def test_vowel_matras():
    assert roman_to_devanagari("ki") == "कि"
    assert roman_to_devanagari("ku") == "कु"
    assert roman_to_devanagari("ke") == "के"
    assert roman_to_devanagari("ko") == "को"


def test_anusvara_and_visarga():
    assert roman_to_devanagari("kaM") == "कं"
    assert roman_to_devanagari("kaH") == "कः"


def test_unrecognized_characters_pass_through():
    assert roman_to_devanagari("k1! ") == "क्1! "


def test_devanagari_to_roman_basic():
    assert devanagari_to_roman("नमस्ते") == "namaste"


def test_roundtrip_for_common_words():
    for word in ["namaste", "ghar", "khaana", "ta", "Ta", "ki", "kaM", "kaH"]:
        deva = roman_to_devanagari(word)
        assert devanagari_to_roman(deva) == word


def test_casual_mode_uses_dictionary_spelling_over_rules():
    # Formal mode gives a "dead" trailing consonant; casual mode looks the
    # word up and uses its real, correctly-spelled Devanagari form instead.
    assert roman_to_devanagari("ghar", casual=True) == "घर"
    assert roman_to_devanagari("cha", casual=True) == "छ"
    assert roman_to_devanagari("xaina", casual=True) == "छैन"


def test_casual_mode_is_case_insensitive_for_proper_nouns():
    # Capital letters used for a sentence-initial/proper-noun word shouldn't
    # be misread as the formal scheme's retroflex signal.
    assert roman_to_devanagari("Aaja", casual=True) == "आज"
    assert roman_to_devanagari("Kathmandu", casual=True) == "काठमाडौं"


def test_casual_mode_leaves_english_loanwords_unchanged():
    assert roman_to_devanagari("office", casual=True) == "office"
    assert roman_to_devanagari("traffic jam", casual=True) == "traffic jam"


def test_casual_mode_full_sentence():
    out = roman_to_devanagari("malai tha xaina", casual=True)
    assert out == "मलाई था छैन"


def test_casual_mode_unknown_word_no_forced_trailing_virama():
    # An out-of-dictionary word ("gham" isn't in the dictionary) falls back
    # to the rule engine, but casual mode doesn't force a dead trailing
    # consonant the way formal mode does.
    assert roman_to_devanagari("gham", casual=True) == "घम"
    assert roman_to_devanagari("gham") == "घम्"  # formal mode, for contrast


def test_formal_mode_default_unaffected_by_casual_mode():
    assert roman_to_devanagari("ghar") == "घर्"
