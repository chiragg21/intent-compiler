"""
dsl_builder.py
==============
Pure functions for building canonical DSL strings.

No imports from other pipeline modules — this file has zero dependencies
within the project so it can be imported anywhere safely.

Public API
----------
  dsl(op, **params)  → str    Build a canonical DSL block
  fuzzy(query)       → str    Build a FUZZY("...") placeholder value
  rename_dsl(...)    → str    Build a RENAME block (special-cased because
                               'from' is a Python reserved word)
  has_fuzzy(s)       → bool   True if string contains a FUZZY placeholder
  extract_intent(s)  → str    Return the operation name from a DSL string
"""

import re


def dsl(op: str, **params) -> str:
    """
    Build a canonical DSL string.

    Rules enforced here:
      - bool  → lowercase true / false
      - int   → unquoted
      - list  → ["a", "b"] (strings only inside lists)
      - None  → null
      - FUZZY → emitted verbatim (already formatted by fuzzy())
      - str   → double-quoted

    Example:
        dsl("MOVE", src="Downloads", dst="Notes", ext="pdf")
        # →
        # MOVE(
        #     src="Downloads",
        #     dst="Notes",
        #     ext="pdf"
        # )
    """
    lines  = [f"{op}("]
    items  = list(params.items())

    for i, (key, value) in enumerate(items):
        comma = "," if i < len(items) - 1 else ""
        val   = _format_value(value)
        lines.append(f"    {key}={val}{comma}")

    lines.append(")")
    return "\n".join(lines)


def fuzzy(query: str) -> str:
    """
    Build a FUZZY placeholder value.

    This is a DSL value type, not an operation.
    It is emitted by the model when the user refers to a file or folder
    by description rather than an explicit path.

    Example:
        fuzzy("resume")  → 'FUZZY("resume")'
    """
    return f'FUZZY("{query}")'


def rename_dsl(path: str, from_str: str, to_str: str, ext: str = "*") -> str:
    """
    Build a RENAME DSL block.

    Special-cased because 'from' is a Python reserved word and cannot
    be passed as a keyword argument to dsl().

    Example:
        rename_dsl("./reports", "draft_", "final_", "docx")
        # →
        # RENAME(
        #     path="./reports",
        #     from="draft_",
        #     to="final_",
        #     ext="docx"
        # )
    """
    params = [
        ("path", f'"{path}"'),
        ("from", f'"{from_str}"'),
        ("to",   f'"{to_str}"'),
        ("ext",  f'"{ext}"'),
    ]
    lines = ["RENAME("]
    for i, (k, v) in enumerate(params):
        comma = "," if i < len(params) - 1 else ""
        lines.append(f"    {k}={v}{comma}")
    lines.append(")")
    return "\n".join(lines)


def has_fuzzy(dsl_str: str) -> bool:
    """Return True if the DSL string contains at least one FUZZY placeholder."""
    return "FUZZY(" in dsl_str


def extract_intent(dsl_str: str) -> str:
    """
    Extract the operation name (intent) from a DSL string.

    Returns "UNKNOWN" if the string does not match expected format.

    Example:
        extract_intent('MOVE(\n    src="Downloads"\n)')  → "MOVE"
    """
    match = re.match(r"^([A-Z][A-Z0-9_]*)\(", dsl_str.strip())
    return match.group(1) if match else "UNKNOWN"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _format_value(value) -> str:
    """Format a Python value into its DSL representation."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        inner = ", ".join(f'"{item}"' for item in value)
        return f"[{inner}]"
    if value is None:
        return "null"
    if isinstance(value, str) and value.startswith("FUZZY("):
        return value  # already formatted, emit verbatim
    if isinstance(value, str):
        return f'"{value}"'
    raise TypeError(f"Unsupported DSL value type: {type(value)} for value {value!r}")