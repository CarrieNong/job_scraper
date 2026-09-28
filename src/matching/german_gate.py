"""
Pre-AI gate: English JDs that explicitly require German as a job language.

If this hits, matching should stop — no stack / years / domain scoring.
Do not treat location, office, company, or market in Germany as a language requirement.
"""
import html as html_module
import re
from typing import Dict, Optional

# Language skill "German" / "Deutsch" — not "Germany".
_GERMAN_SKILL = re.compile(
    r"\b(?:german|deutsch\w*)\b",
    re.I,
)

# Nearby text that means German is being asked as a language skill.
_LANGUAGE_CONTEXT = re.compile(
    r"\b(?:"
    r"language|languages|speak|speaking|speaker|spoken|"
    r"fluency|fluent|native|proficiency|proficient|"
    r"level|kenntnisse|skills?|written|oral|verbal|"
    r"c1|c2|b1|b2|a2|"
    r"muttersprach|flie[sß]end|verhandlungssicher"
    r")\b",
    re.I,
)

_MANDATORY = re.compile(
    r"\b(?:"
    r"required|requirement|mandatory|must[- ]have|must have|"
    r"must be|must speak|need to|needs to|you must|we require|"
    r"essential|necessary|minimum|at least|"
    r"erforderlich|zwingend|notwendig|"
    r"native|fluent|fluency|proficient|proficiency|"
    r"business[- ]fluent|professional(?:\s+working)?\s+proficiency|"
    r"c1|c2|b2|"
    r"muttersprach|flie[sß]end|verhandlungssicher"
    r")\b",
    re.I,
)

# Explicit CEFR / fluency phrasing attached to German.
_LEVEL_OR_FLUENT = re.compile(
    r"(?:"
    r"\b(?:c1|c2|b2|b1)\b|"
    r"\b(?:fluent|fluency|native|proficient|proficiency)\b|"
    r"\bbusiness[- ]fluent\b|"
    r"\bvery good\b|\bexcellent\b|"
    r"\bflie[sß]end\b|\bmuttersprach"
    r")",
    re.I,
)

_OPTIONAL = re.compile(
    r"\b(?:"
    r"nice[- ]to[- ]have|advantage|preferred|preferably|"
    r"beneficial|bonus|ideally|optional|"
    r"not required|not mandatory|"
    r"(?:a|is a|would be a)\s+plus"
    r")\b",
    re.I,
)

# "German office / customers / market / company" is not a language skill.
_NOT_LANGUAGE = re.compile(
    r"\bgerman\s+(?:office|offices|hq|headquarters|market|markets|"
    r"customer|customers|client|clients|brand|brands|"
    r"company|companies|startup|team|engineering team|"
    r"public[- ]transport|gym|perk)\b",
    re.I,
)

_WINDOW = 110


def _plain_text(html_text: str) -> str:
    if not html_text:
        return ""
    text = re.sub(
        r"<(style|script)[^>]*>.*?</\1>",
        " ",
        html_text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_module.unescape(text)
    return " ".join(text.split())


def _snippet(text: str, start: int, end: int, pad: int = 40) -> str:
    lo = max(0, start - pad)
    hi = min(len(text), end + pad)
    chunk = " ".join(text[lo:hi].split())
    if lo > 0:
        chunk = "…" + chunk
    if hi < len(text):
        chunk = chunk + "…"
    return chunk[:180]


def find_mandatory_german_requirement(job: Dict) -> Optional[str]:
    """
    Return a short disqualification reason if the JD explicitly requires
    German as a job language (must-have / fluent / native / CEFR level).

    Returns None when German is absent, nice-to-have, or only appears as
    location / office / company / market.
    """
    raw = " ".join(
        str(part or "")
        for part in (
            job.get("title"),
            job.get("location"),
            job.get("description"),
        )
    )
    text = _plain_text(raw)
    if not text or not _GERMAN_SKILL.search(text):
        return None

    for match in _GERMAN_SKILL.finditer(text):
        # "Germany" is a different token; \bgerman\b already excludes it.
        start, end = match.start(), match.end()
        window = text[max(0, start - _WINDOW) : min(len(text), end + _WINDOW)]
        optional_window = text[max(0, start - 50) : min(len(text), end + 50)]

        if _NOT_LANGUAGE.search(window):
            # Still a hit if the same window clearly asks for the language.
            if not _LANGUAGE_CONTEXT.search(window):
                continue

        if _OPTIONAL.search(optional_window):
            continue

        is_language = bool(_LANGUAGE_CONTEXT.search(window))
        is_mandatory = bool(_MANDATORY.search(window))
        has_level = bool(_LEVEL_OR_FLUENT.search(window))
        listed_as_language = bool(
            re.search(r"\blanguages?\s*[:\-–]", window, re.I)
        )

        if (is_language or listed_as_language) and (is_mandatory or has_level):
            snippet = _snippet(text, start, end)
            return (
                "Mandatory German language requirement "
                f"(candidate does not speak German): \"{snippet}\""
            )

        # Strong collocations even without a separate "language" word.
        strong = re.search(
            r"(?:"
            r"fluent(?:ly)?\s+in\s+german|"
            r"german\s+(?:language\s+)?(?:skills?\s+)?(?:required|mandatory|essential|necessary)|"
            r"must\s+(?:speak|have|be)\s+german|"
            r"(?:working\s+)?languages?\s+(?:is|are)\s+german|"
            r"german\s+as\s+(?:a\s+)?(?:working\s+)?language|"
            r"deutsch(?:kenntnisse)?\s*[:\-–]?\s*(?:flie[sß]end|c1|c2|b2|muttersprach|erforderlich)"
            r")",
            window,
            re.I,
        )
        if strong:
            snippet = _snippet(text, start, end)
            return (
                "Mandatory German language requirement "
                f"(candidate does not speak German): \"{snippet}\""
            )

    return None


def german_disqualification_analysis(reason: str) -> Dict:
    """Minimal analysis payload — no stack / years scoring."""
    return {
        "match_score": 1.0,
        "recommendation": "No",
        "special_match": False,
        "special_match_reasons": [],
        "disqualification_reason": reason,
        "what_youll_do": {"matched": [], "unmatched": []},
        "what_theyre_looking_for": {
            "matched": [],
            "unmatched": ["German as a mandatory job-language requirement"],
        },
        "match_reasons": [],
        "missing_requirements": ["German (mandatory job language)"],
        "red_flags": ["Mandatory German language requirement — skipped remaining matching"],
        "nice_to_have_matches": [],
        "summary": "Stopped at German language gate; other requirements were not evaluated.",
    }
