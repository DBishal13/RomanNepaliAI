"""Roman <-> Devanagari transliteration for Nepali.

Two modes are offered:

- Formal mode (default, `casual=False`): a fixed, ITRANS/Harvard-Kyoto-inspired
  romanization scheme. One canonical spelling maps to one Devanagari
  rendering, purely by rule -- no dictionary, no guessing. Case matters
  (retroflex consonants are capitalized: T/D/N/Th/Dh vs t/d/n/th/dh) and a
  consonant with no following vowel becomes a "dead" (virama-joined)
  consonant rather than getting an implicit inherent "a".

- Casual mode (`casual=True`): tuned for free-typed, texting-style romanized
  Nepali (e.g. "malai tha xaina", "Aaja office jana man lagdaina") where
  capitalization is inconsistent (just proper nouns / sentence starts, not a
  retroflex signal), English loanwords are mixed in, and words are spelled
  however sounds right. It works word-by-word:
    1. Known common words are looked up in a curated dictionary and rendered
       with their real, correctly-spelled Devanagari form.
    2. Known English loanwords are left in Latin script unchanged, matching
       common Nepali texting/subtitle practice.
    3. Anything else falls back to the formal rule engine, but
       case-INsensitive and without forcing a dead trailing consonant (a
       word-final consonant gets its natural inherent vowel instead of a
       virama).
  This is inherently a best-effort heuristic, not a full NLP model -- unknown
  words outside the dictionary are still transliterated syllable-by-syllable
  and won't always match real Nepali orthography (e.g. schwa deletion rules
  are not modeled beyond word-final position).

In both modes, unrecognized characters (digits, punctuation, whitespace,
already-Devanagari text, etc.) pass through unchanged.
"""
import re
from typing import Dict, List, Tuple

VIRAMA = "्"
ANUSVARA = "ं"
VISARGA = "ः"

# roman -> devanagari consonant (can be a multi-codepoint conjunct, e.g. ksh/gy)
_CONSONANTS: Dict[str, str] = {
    "ksh": "क्ष",
    "gy": "ज्ञ",
    "kh": "ख", "gh": "घ", "ng": "ङ",
    "chh": "छ",
    "jh": "झ", "ny": "ञ",
    "Th": "ठ", "Dh": "ढ",
    "th": "थ", "dh": "ध",
    "ph": "फ", "bh": "भ",
    "sh": "श", "Sh": "ष",
    "ch": "च",
    "k": "क", "g": "ग", "c": "च", "j": "ज",
    "T": "ट", "D": "ड", "N": "ण",
    "t": "त", "d": "द", "n": "न",
    "p": "प", "b": "ब", "m": "म",
    "y": "य", "r": "र", "l": "ल",
    "v": "व", "w": "व",
    "s": "स", "h": "ह",
    "x": "छ",  # colloquial Nepali texting spelling for the "chh" sound
}

# roman -> (independent vowel form, dependent matra form; matra is '' for inherent "a")
_VOWELS: Dict[str, Tuple[str, str]] = {
    "aa": ("आ", "ा"), "ai": ("ऐ", "ै"), "au": ("औ", "ौ"),
    "ii": ("ई", "ी"), "uu": ("ऊ", "ू"),
    "a": ("अ", ""), "i": ("इ", "ि"), "u": ("उ", "ु"),
    "e": ("ए", "े"), "o": ("ओ", "ो"),
}

# forward-only aliases for the vowel table above (not used for the reverse mapping)
_VOWEL_ALIASES: Dict[str, str] = {
    "A": "aa", "I": "ii", "U": "uu", "ee": "ii", "oo": "uu",
}

_SPECIALS: Dict[str, str] = {"M": ANUSVARA, "H": VISARGA}

# Tokens sorted longest-first so e.g. "chh" is matched before "ch" before "c".
_TOKENS: List[Tuple[str, str, object]] = []
for _roman, _dev in _CONSONANTS.items():
    _TOKENS.append((_roman, "C", _dev))
for _roman, _val in _VOWELS.items():
    _TOKENS.append((_roman, "V", _val))
for _alias, _canonical in _VOWEL_ALIASES.items():
    _TOKENS.append((_alias, "V", _VOWELS[_canonical]))
for _roman, _dev in _SPECIALS.items():
    _TOKENS.append((_roman, "S", _dev))
_TOKENS.sort(key=lambda t: -len(t[0]))

# Case-insensitive token table used by casual mode's fallback path: lowercased
# roman spelling -> the token that lowercases to it. When both a dental and a
# retroflex spelling collapse to the same lowercase key (e.g. "t" and "T"),
# prefer the dental one -- it's the overwhelmingly common case in casual
# romanized Nepali, and retroflex marking requires a deliberate capital that
# casual mode explicitly doesn't trust. Already-lowercase tokens are tried
# before ones that needed lowercasing, so e.g. "t" wins over "T".
_TOKENS_CI: List[Tuple[str, str, object]] = []
_seen_ci: Dict[str, bool] = {}
for _roman, _kind, _val in sorted(_TOKENS, key=lambda t: t[0] != t[0].lower()):
    _lroman = _roman.lower()
    if _lroman not in _seen_ci:
        _seen_ci[_lroman] = True
        _TOKENS_CI.append((_lroman, _kind, _val))
_TOKENS_CI.sort(key=lambda t: -len(t[0]))

# Reverse lookups (Devanagari -> canonical roman), built from canonical tables only.
_CONSONANT_REV: Dict[str, str] = {}
for _roman, _dev in _CONSONANTS.items():
    if len(_dev) == 1 and _dev not in _CONSONANT_REV:
        _CONSONANT_REV[_dev] = _roman

_INDEP_VOWEL_REV: Dict[str, str] = {}
_MATRA_REV: Dict[str, str] = {}
for _roman, (_indep, _matra) in _VOWELS.items():
    _INDEP_VOWEL_REV.setdefault(_indep, _roman)
    if _matra:
        _MATRA_REV.setdefault(_matra, _roman)

# Curated common-word dictionary for casual mode: casual romanization (lowercase)
# -> correctly-spelled Devanagari. Several roman variants may point at the same
# word (e.g. "xaina"/"chaina"). This is necessarily a small, high-frequency
# subset, not exhaustive -- extend it as more real-world input is seen.
_COMMON_WORDS: Dict[str, str] = {
    "ma": "म", "hami": "हामी", "timi": "तिमी", "tapai": "तपाईं", "tapaii": "तपाईं",
    "u": "ऊ", "uni": "उनी", "hajur": "हजुर",
    "ghar": "घर", "malai": "मलाई", "tyo": "त्यो", "yo": "यो",
    "tha": "था", "thaha": "थाहा",
    "xaina": "छैन", "chaina": "छैन", "chhaina": "छैन",
    "cha": "छ", "chha": "छ", "chu": "छु", "chhu": "छु", "chau": "छौ", "chhau": "छौ",
    "huncha": "हुन्छ", "huhuncha": "हुन्छ", "hudaina": "हुँदैन", "hunu": "हुनु",
    "hunuhuncha": "हुनुहुन्छ",
    "ramro": "राम्रो", "ramailo": "रमाइलो", "thulo": "ठूलो", "sano": "सानो",
    "asal": "असल", "naramro": "नराम्रो",
    "k": "के", "ke": "के", "kina": "किन", "kaha": "कहाँ", "kahan": "कहाँ",
    "kahile": "कहिले", "kasari": "कसरी", "kasto": "कस्तो", "kati": "कति", "kun": "कुन",
    "gardai": "गर्दै", "garne": "गर्ने", "garchu": "गर्छु", "garcha": "गर्छ", "garxa": "गर्छ",
    "gaye": "गए", "gayo": "गयो", "jane": "जाने", "jana": "जान", "aune": "आउने",
    "aayo": "आयो", "aaya": "आयो",
    "aaja": "आज", "aja": "आज", "hijo": "हिजो", "bholi": "भोलि",
    "man": "मन", "lagdaina": "लाग्दैन", "lagyo": "लाग्यो", "lagcha": "लाग्छ",
    "kathmandu": "काठमाडौं", "nepal": "नेपाल", "pokhara": "पोखरा",
    "ko": "को", "ki": "की", "ka": "का",
    "mausam": "मौसम", "momo": "मोमो", "khane": "खाने", "khana": "खाना", "khanu": "खानु",
    "dashain": "दशैं", "tihar": "तिहार", "maneko": "मनेको",
    "dal": "दाल", "bhat": "भात", "baseko": "बसेको",
    "pani": "पनि", "paani": "पानी", "ali": "अलि", "dherai": "धेरै",
    "ghumna": "घुम्न", "sathi": "साथी", "vayo": "भयो", "bhayo": "भयो",
    "sanchai": "सन्चै", "dhanyabad": "धन्यवाद", "maaf": "माफ",
    "naam": "नाम", "mero": "मेरो", "ho": "हो", "timro": "तिम्रो", "hamro": "हाम्रो",
}

# English loanwords commonly code-switched into Nepali sentences: left in
# Latin script unchanged rather than transliterated into gibberish syllables.
_ENGLISH_LOANWORDS = {
    "office", "power", "hour", "traffic", "jam", "internet", "mobile",
    "computer", "tv", "bus", "car", "style", "plan", "set", "full", "best",
    "sorry", "thanks", "thank", "you", "ok", "okay", "hi", "hello", "bye",
    "game", "team", "party", "photo", "video", "school", "college",
    "hospital", "doctor", "table", "chair", "phone", "call", "message",
    "email", "meeting", "project", "deadline", "boss", "salary", "bank",
    "market", "shop", "ticket", "movie", "hotel", "restaurant", "taxi",
    "bike", "internet", "wifi", "password", "please",
}


def _tokenize(text: str, tokens: List[Tuple[str, str, object]]) -> List[Tuple[str, str, object]]:
    out = []
    i = 0
    n = len(text)
    while i < n:
        for roman, kind, val in tokens:
            length = len(roman)
            if text[i:i + length] == roman:
                out.append((kind, roman, val))
                i += length
                break
        else:
            out.append(("O", text[i], text[i]))
            i += 1
    return out


def _convert(text: str, token_table: List[Tuple[str, str, object]], drop_trailing_virama: bool = False) -> str:
    tokens = _tokenize(text, token_table)
    out = []
    i = 0
    n = len(tokens)
    while i < n:
        kind, roman, val = tokens[i]
        if kind == "C":
            base = val
            nxt = tokens[i + 1] if i + 1 < n else None
            if nxt and nxt[0] == "V":
                vroman, (indep, matra) = nxt[1], nxt[2]
                out.append(base if vroman == "a" else base + matra)
                i += 2
            elif nxt and nxt[0] == "S":
                out.append(base)
                out.append(nxt[2])
                i += 2
            else:
                out.append(base + VIRAMA)
                i += 1
        elif kind == "V":
            indep, _matra = val
            out.append(indep)
            i += 1
        elif kind == "S":
            out.append(val)
            i += 1
        else:  # 'O' -- unrecognized, pass through
            out.append(val)
            i += 1
    if drop_trailing_virama and out and out[-1].endswith(VIRAMA):
        out[-1] = out[-1][:-len(VIRAMA)]
    return "".join(out)


_WORD_RE = re.compile(r"^(\W*)(\w*)(\W*)$", re.UNICODE)


def _roman_to_devanagari_casual(text: str) -> str:
    parts = re.split(r"(\s+)", text)
    out = []
    for part in parts:
        if part == "" or part.isspace():
            out.append(part)
            continue
        m = _WORD_RE.match(part)
        prefix, core, suffix = m.groups() if m else ("", part, "")
        if not core:
            out.append(part)
            continue
        lw = core.lower()
        if lw in _COMMON_WORDS:
            out.append(prefix + _COMMON_WORDS[lw] + suffix)
        elif lw in _ENGLISH_LOANWORDS:
            out.append(part)
        else:
            out.append(prefix + _convert(lw, _TOKENS_CI, drop_trailing_virama=True) + suffix)
    return "".join(out)


def roman_to_devanagari(text: str, casual: bool = False) -> str:
    """Transliterate romanized text into Devanagari.

    By default uses the fixed, case-sensitive formal scheme (see module
    docstring). Pass `casual=True` for free-typed romanized Nepali: common
    words are looked up in a curated dictionary, English loanwords are left
    unchanged, and unknown words are matched case-insensitively without a
    forced dead trailing consonant.
    """
    if casual:
        return _roman_to_devanagari_casual(text)
    return _convert(text, _TOKENS, drop_trailing_virama=False)


def devanagari_to_roman(text: str) -> str:
    """Best-effort inverse of roman_to_devanagari's formal-mode output.

    Not guaranteed to reproduce the exact original spelling when multiple
    romanizations map to the same Devanagari (e.g. both "v" and "w" -> व;
    the canonical one is emitted), and not a meaningful inverse of casual-mode
    output (dictionary lookups and loanword passthrough aren't invertible).
    """
    out = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch in _CONSONANT_REV:
            roman = _CONSONANT_REV[ch]
            nxt = text[i + 1] if i + 1 < n else ""
            if nxt == VIRAMA:
                out.append(roman)
                i += 2
            elif nxt in _MATRA_REV:
                out.append(roman + _MATRA_REV[nxt])
                i += 2
            elif nxt == ANUSVARA:
                out.append(roman + "a" + "M")
                i += 2
            elif nxt == VISARGA:
                out.append(roman + "a" + "H")
                i += 2
            else:
                out.append(roman + "a")
                i += 1
        elif ch in _INDEP_VOWEL_REV:
            out.append(_INDEP_VOWEL_REV[ch])
            i += 1
        elif ch == ANUSVARA:
            out.append("M")
            i += 1
        elif ch == VISARGA:
            out.append("H")
            i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)
