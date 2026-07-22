// Client-side port of src/roman_nepali_ai/transliterate.py.
// Keep this in sync with the Python module -- same tables, same algorithm.
(function (global) {
  "use strict";

  const VIRAMA = "्";
  const ANUSVARA = "ं";
  const VISARGA = "ः";

  const CONSONANTS = {
    ksh: "क्ष",
    gy: "ज्ञ",
    kh: "ख", gh: "घ", ng: "ङ",
    chh: "छ",
    jh: "झ", ny: "ञ",
    Th: "ठ", Dh: "ढ",
    th: "थ", dh: "ध",
    ph: "फ", bh: "भ",
    sh: "श", Sh: "ष",
    ch: "च",
    k: "क", g: "ग", c: "च", j: "ज",
    T: "ट", D: "ड", N: "ण",
    t: "त", d: "द", n: "न",
    p: "प", b: "ब", m: "म",
    y: "य", r: "र", l: "ल",
    v: "व", w: "व",
    s: "स", h: "ह",
    x: "छ", // colloquial Nepali texting spelling for the "chh" sound
  };

  // roman -> [independent vowel form, dependent matra form] (matra "" = inherent "a")
  const VOWELS = {
    aa: ["आ", "ा"], ai: ["ऐ", "ै"], au: ["औ", "ौ"],
    ii: ["ई", "ी"], uu: ["ऊ", "ू"],
    a: ["अ", ""], i: ["इ", "ि"], u: ["उ", "ु"],
    e: ["ए", "े"], o: ["ओ", "ो"],
  };

  // forward-only aliases (not used for the reverse mapping)
  const VOWEL_ALIASES = { A: "aa", I: "ii", U: "uu", ee: "ii", oo: "uu" };

  const SPECIALS = { M: ANUSVARA, H: VISARGA };

  // Curated common-word dictionary for casual mode: casual romanization
  // (lowercase) -> correctly-spelled Devanagari.
  const COMMON_WORDS = {
    ma: "म", hami: "हामी", timi: "तिमी", tapai: "तपाईं", tapaii: "तपाईं",
    u: "ऊ", uni: "उनी", hajur: "हजुर",
    ghar: "घर", malai: "मलाई", tyo: "त्यो", yo: "यो",
    tha: "था", thaha: "थाहा",
    xaina: "छैन", chaina: "छैन", chhaina: "छैन",
    cha: "छ", chha: "छ", chu: "छु", chhu: "छु", chau: "छौ", chhau: "छौ",
    huncha: "हुन्छ", huhuncha: "हुन्छ", hudaina: "हुँदैन", hunu: "हुनु",
    hunuhuncha: "हुनुहुन्छ",
    ramro: "राम्रो", ramailo: "रमाइलो", thulo: "ठूलो", sano: "सानो",
    asal: "असल", naramro: "नराम्रो",
    k: "के", ke: "के", kina: "किन", kaha: "कहाँ", kahan: "कहाँ",
    kahile: "कहिले", kasari: "कसरी", kasto: "कस्तो", kati: "कति", kun: "कुन",
    gardai: "गर्दै", garne: "गर्ने", garchu: "गर्छु", garcha: "गर्छ", garxa: "गर्छ",
    gaye: "गए", gayo: "गयो", jane: "जाने", jana: "जान", aune: "आउने",
    aayo: "आयो", aaya: "आयो",
    aaja: "आज", aja: "आज", hijo: "हिजो", bholi: "भोलि",
    man: "मन", lagdaina: "लाग्दैन", lagyo: "लाग्यो", lagcha: "लाग्छ",
    kathmandu: "काठमाडौं", nepal: "नेपाल", pokhara: "पोखरा",
    ko: "को", ki: "की", ka: "का",
    mausam: "मौसम", momo: "मोमो", khane: "खाने", khana: "खाना", khanu: "खानु",
    dashain: "दशैं", tihar: "तिहार", maneko: "मनेको",
    dal: "दाल", bhat: "भात", baseko: "बसेको",
    pani: "पनि", paani: "पानी", ali: "अलि", dherai: "धेरै",
    ghumna: "घुम्न", sathi: "साथी", vayo: "भयो", bhayo: "भयो",
    sanchai: "सन्चै", dhanyabad: "धन्यवाद", maaf: "माफ",
    naam: "नाम", mero: "मेरो", ho: "हो", timro: "तिम्रो", hamro: "हाम्रो",
  };

  const ENGLISH_LOANWORDS = new Set([
    "office", "power", "hour", "traffic", "jam", "internet", "mobile",
    "computer", "tv", "bus", "car", "style", "plan", "set", "full", "best",
    "sorry", "thanks", "thank", "you", "ok", "okay", "hi", "hello", "bye",
    "game", "team", "party", "photo", "video", "school", "college",
    "hospital", "doctor", "table", "chair", "phone", "call", "message",
    "email", "meeting", "project", "deadline", "boss", "salary", "bank",
    "market", "shop", "ticket", "movie", "hotel", "restaurant", "taxi",
    "bike", "wifi", "password", "please",
  ]);

  function buildTokens() {
    const tokens = [];
    for (const [roman, dev] of Object.entries(CONSONANTS)) {
      tokens.push({ roman, kind: "C", val: dev });
    }
    for (const [roman, val] of Object.entries(VOWELS)) {
      tokens.push({ roman, kind: "V", val });
    }
    for (const [alias, canonical] of Object.entries(VOWEL_ALIASES)) {
      tokens.push({ roman: alias, kind: "V", val: VOWELS[canonical] });
    }
    for (const [roman, dev] of Object.entries(SPECIALS)) {
      tokens.push({ roman, kind: "S", val: dev });
    }
    tokens.sort((a, b) => b.roman.length - a.roman.length);
    return tokens;
  }

  const TOKENS = buildTokens();

  function buildTokensCI() {
    // Prefer already-lowercase tokens over ones that needed lowercasing, so
    // e.g. dental "t"/"d"/"n" win over retroflex "T"/"D"/"N" when both
    // collapse to the same lowercase key -- dental is the overwhelmingly
    // common case in casual romanized Nepali.
    const ordered = [...TOKENS].sort((a, b) => {
      const aLower = a.roman === a.roman.toLowerCase() ? 0 : 1;
      const bLower = b.roman === b.roman.toLowerCase() ? 0 : 1;
      return aLower - bLower;
    });
    const seen = new Set();
    const out = [];
    for (const t of ordered) {
      const lroman = t.roman.toLowerCase();
      if (!seen.has(lroman)) {
        seen.add(lroman);
        out.push({ roman: lroman, kind: t.kind, val: t.val });
      }
    }
    out.sort((a, b) => b.roman.length - a.roman.length);
    return out;
  }

  const TOKENS_CI = buildTokensCI();

  const CONSONANT_REV = {};
  for (const [roman, dev] of Object.entries(CONSONANTS)) {
    if (dev.length === 1 && !(dev in CONSONANT_REV)) {
      CONSONANT_REV[dev] = roman;
    }
  }

  const INDEP_VOWEL_REV = {};
  const MATRA_REV = {};
  for (const [roman, [indep, matra]] of Object.entries(VOWELS)) {
    if (!(indep in INDEP_VOWEL_REV)) INDEP_VOWEL_REV[indep] = roman;
    if (matra && !(matra in MATRA_REV)) MATRA_REV[matra] = roman;
  }

  function tokenize(text, tokenTable) {
    const out = [];
    let i = 0;
    const n = text.length;
    while (i < n) {
      let matched = false;
      for (const t of tokenTable) {
        const len = t.roman.length;
        if (text.substr(i, len) === t.roman) {
          out.push(t);
          i += len;
          matched = true;
          break;
        }
      }
      if (!matched) {
        out.push({ roman: text[i], kind: "O", val: text[i] });
        i += 1;
      }
    }
    return out;
  }

  function convert(text, tokenTable, dropTrailingVirama) {
    const tokens = tokenize(text, tokenTable);
    const out = [];
    let i = 0;
    const n = tokens.length;
    while (i < n) {
      const { kind, val } = tokens[i];
      if (kind === "C") {
        const base = val;
        const nxt = i + 1 < n ? tokens[i + 1] : null;
        if (nxt && nxt.kind === "V") {
          const [, matra] = nxt.val;
          out.push(nxt.roman === "a" ? base : base + matra);
          i += 2;
        } else if (nxt && nxt.kind === "S") {
          out.push(base);
          out.push(nxt.val);
          i += 2;
        } else {
          out.push(base + VIRAMA);
          i += 1;
        }
      } else if (kind === "V") {
        out.push(val[0]);
        i += 1;
      } else if (kind === "S") {
        out.push(val);
        i += 1;
      } else {
        out.push(val);
        i += 1;
      }
    }
    if (dropTrailingVirama && out.length && out[out.length - 1].endsWith(VIRAMA)) {
      const last = out[out.length - 1];
      out[out.length - 1] = last.slice(0, -VIRAMA.length);
    }
    return out.join("");
  }

  const WORD_RE = /^(\W*)(\w*)(\W*)$/;

  function romanToDevanagariCasual(text) {
    const parts = text.split(/(\s+)/);
    const out = [];
    for (const part of parts) {
      if (part === "" || /^\s+$/.test(part)) {
        out.push(part);
        continue;
      }
      const m = WORD_RE.exec(part);
      const prefix = m ? m[1] : "";
      const core = m ? m[2] : part;
      const suffix = m ? m[3] : "";
      if (!core) {
        out.push(part);
        continue;
      }
      const lw = core.toLowerCase();
      if (Object.prototype.hasOwnProperty.call(COMMON_WORDS, lw)) {
        out.push(prefix + COMMON_WORDS[lw] + suffix);
      } else if (ENGLISH_LOANWORDS.has(lw)) {
        out.push(part);
      } else {
        out.push(prefix + convert(lw, TOKENS_CI, true) + suffix);
      }
    }
    return out.join("");
  }

  function romanToDevanagari(text, casual) {
    if (casual) return romanToDevanagariCasual(text);
    return convert(text, TOKENS, false);
  }

  function devanagariToRoman(text) {
    const out = [];
    let i = 0;
    const n = text.length;
    while (i < n) {
      const ch = text[i];
      if (ch in CONSONANT_REV) {
        const roman = CONSONANT_REV[ch];
        const nxt = i + 1 < n ? text[i + 1] : "";
        if (nxt === VIRAMA) {
          out.push(roman);
          i += 2;
        } else if (nxt in MATRA_REV) {
          out.push(roman + MATRA_REV[nxt]);
          i += 2;
        } else if (nxt === ANUSVARA) {
          out.push(roman + "a" + "M");
          i += 2;
        } else if (nxt === VISARGA) {
          out.push(roman + "a" + "H");
          i += 2;
        } else {
          out.push(roman + "a");
          i += 1;
        }
      } else if (ch in INDEP_VOWEL_REV) {
        out.push(INDEP_VOWEL_REV[ch]);
        i += 1;
      } else if (ch === ANUSVARA) {
        out.push("M");
        i += 1;
      } else if (ch === VISARGA) {
        out.push("H");
        i += 1;
      } else {
        out.push(ch);
        i += 1;
      }
    }
    return out.join("");
  }

  global.RomanNepaliAI = { romanToDevanagari, devanagariToRoman };
})(window);
