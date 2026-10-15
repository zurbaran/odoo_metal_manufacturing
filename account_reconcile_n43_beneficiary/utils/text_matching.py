# Copyright 2026 Camarbax
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import re

MATCH_TYPES = [
    ("starts_with", "Starts with"),
    ("contains", "Contains"),
    ("ends_with", "Ends with"),
    ("exact", "Exactly equals"),
    ("regex", "Advanced Python regular expression"),
]


def matches(kind, pattern, value, case_sensitive=False, legacy=None):
    """Execute readable rules in Python in both versions, never as SQL regexes.

    Advanced expressions retain Python re.match semantics. Only an explicit
    migration snapshot can request the old 19.0 port's re.search/IGNORECASE.
    """
    value = value or ""
    pattern = pattern or ""
    if kind == "regex":
        legacy = legacy or {}
        method = re.search if legacy.get("search") else re.match
        flags = re.IGNORECASE if legacy.get("ignore_case") else 0
        return bool(method(pattern, value, flags))
    legacy = legacy or {}
    if not case_sensitive and legacy.get("casefold"):
        value, pattern = value.casefold(), pattern.casefold()
        case_sensitive = True
    if not case_sensitive and legacy.get("lower"):
        value, pattern = value.lower(), pattern.lower()
        case_sensitive = not legacy.get("ignore_case")
    literal = re.escape(pattern)
    if kind in ("starts_with", "exact"):
        literal = r"\A" + literal
    if kind in ("ends_with", "exact"):
        literal += r"\Z"
    if kind not in {"starts_with", "contains", "ends_with", "exact"}:
        raise ValueError("Unknown text matching operation")
    flags = 0 if case_sensitive else re.IGNORECASE
    if legacy.get("ascii_case"):
        flags |= re.ASCII
    return bool(re.search(literal, value, flags))


def simple_prefix(pattern):
    """Recognize only provably literal, anchored prefix expressions.

    No general regex rewriting: whitespace classes, alternatives, end anchors,
    mixed case sensitivity and other constructs stay advanced.
    """
    pattern = pattern or ""
    ignore_case = pattern.startswith("(?i)")
    if ignore_case:
        pattern = pattern[4:]
    if pattern.startswith(r"\A"):
        pattern = pattern[2:]
    elif pattern.startswith("^"):
        pattern = pattern[1:]
    else:
        return None
    if pattern.endswith(".*"):
        pattern = pattern[:-2]
    result = []
    sensitivity = set()
    while pattern:
        if pattern.startswith("["):
            pair = pattern[:4]
            if (
                len(pair) != 4
                or pair[-1] != "]"
                or not pair[1:3].isascii()
                or not pair[1:3].isalpha()
                or pair[1] == pair[2]
                or pair[1].lower() != pair[2].lower()
            ):
                return None
            result.append(pair[1].upper())
            sensitivity.add(False)
            pattern = pattern[4:]
        elif pattern.startswith("\\"):
            if len(pattern) < 2 or pattern[1] not in ".-/ _":
                return None
            result.append(pattern[1])
            pattern = pattern[2:]
        elif pattern[0] in ".^$*+?{}[]()|\\":
            return None
        else:
            char = pattern[0]
            if not char.isascii():
                return None
            result.append(char)
            if char.isalpha():
                sensitivity.add(not ignore_case)
            pattern = pattern[1:]
    if not result or len(sensitivity) > 1:
        return None
    return "".join(result), (sensitivity == {True}), not ignore_case
