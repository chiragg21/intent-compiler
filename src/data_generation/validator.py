"""
validator.py
============
Structural validation of DSL strings and dataset records.

Used by gold.py, synthetic.py, and run.py to catch malformed output
before it enters training data.

Public API
----------
  validate_dsl(dsl_str)          → (ok: bool, reason: str)
  validate_record(record)        → (ok: bool, reason: str)
  validate_dataset(records)      → list[ValidationError]
  print_validation_report(errors)
"""

import re
from dataclasses import dataclass
from typing import Optional


# Operations that must have confirm=true
REQUIRES_CONFIRM: set[str] = {"DELETE", "SYS_KILL", "DEV_CLEAN"}

# All registered operation names — update when adding new operations
KNOWN_OPERATIONS: set[str] = {
    "MOVE", "COPY", "RENAME", "DELETE", "COMPRESS", "EXTRACT", "SEARCH",
    "GIT_INIT", "GIT_CLONE", "GIT_COMMIT", "GIT_PUSH", "GIT_BRANCH", "GIT_CHECKOUT",
    "PY_VENV", "PY_INSTALL", "PY_TEST", "PY_NOTEBOOK",
    "SYS_OPEN", "SYS_KILL", "SYS_STORAGE", "SYS_MEMORY",
    "DEV_ORGANIZE", "DEV_CLEAN", "DEV_ARCHIVE_LOGS",
}

# Required fields in every dataset record
REQUIRED_RECORD_FIELDS: set[str] = {
    "id", "tier", "intent", "input", "output", "source", "has_fuzzy",
}


@dataclass
class ValidationError:
    record_id: str
    reason:    str
    field:     str          # "dsl" | "record" | specific field name
    snippet:   Optional[str] = None   # first 80 chars of bad value


# ---------------------------------------------------------------------------
# DSL-level validation
# ---------------------------------------------------------------------------

def validate_dsl(dsl_str: str) -> tuple[bool, str]:
    """
    Structural validation of a single DSL string.

    Checks:
      1. Non-empty (OOD records have empty output — always pass)
      2. Header line: OPERATION_NAME(
      3. Footer line: )
      4. Parameter lines: 4-space indent, name=value format
      5. No single quotes anywhere
      6. Operation name is in KNOWN_OPERATIONS
      7. Destructive ops have confirm=true

    Returns (True, "ok") on success, (False, reason) on failure.
    """
    if not dsl_str or not dsl_str.strip():
        return True, "ok"   # empty output is valid for OOD records

    lines = dsl_str.strip().split("\n")

    # ── header ──────────────────────────────────────────────────────────────
    if not re.match(r"^[A-Z][A-Z0-9_]*\($", lines[0]):
        return False, f"bad header line: '{lines[0]}'"

    op_name = lines[0].rstrip("(")

    # ── known operation ──────────────────────────────────────────────────────
    if op_name not in KNOWN_OPERATIONS:
        return False, f"unknown operation: '{op_name}'"

    # ── footer ───────────────────────────────────────────────────────────────
    if lines[-1] != ")":
        return False, f"bad footer line: '{lines[-1]}'"

    # ── parameter lines ──────────────────────────────────────────────────────
    for line in lines[1:-1]:
        if not line.startswith("    "):
            return False, f"bad indentation: '{line}'"
        if not re.match(r"^    [a-z][a-z0-9_]*=.+,?$", line):
            return False, f"bad parameter line: '{line}'"

    # ── no single quotes ─────────────────────────────────────────────────────
    if "'" in dsl_str:
        return False, "single quotes found — all strings must use double quotes"

    # ── destructive ops must have confirm=true ────────────────────────────────
    if op_name in REQUIRES_CONFIRM:
        if "confirm=true" not in dsl_str:
            return False, f"{op_name} is a destructive operation — confirm=true is required"

    return True, "ok"


# ---------------------------------------------------------------------------
# Record-level validation
# ---------------------------------------------------------------------------

def validate_record(record: dict) -> tuple[bool, str]:
    """
    Validate a single dataset record dict.

    Checks:
      1. All required fields are present
      2. 'tier' is one of: gold | synthetic | ood
      3. 'source' is one of: manual | template | paraphrase
      4. 'has_fuzzy' matches actual DSL content
      5. DSL structural validation (delegates to validate_dsl)
    """
    # required fields
    missing = REQUIRED_RECORD_FIELDS - set(record.keys())
    if missing:
        return False, f"missing fields: {missing}"

    # tier
    if record["tier"] not in {"gold", "synthetic", "ood"}:
        return False, f"invalid tier: '{record['tier']}'"

    # source
    if record["source"] not in {"manual", "template", "paraphrase"}:
        return False, f"invalid source: '{record['source']}'"

    # has_fuzzy consistency
    actual_fuzzy = "FUZZY(" in record.get("output", "")
    if record["has_fuzzy"] != actual_fuzzy:
        return False, (
            f"has_fuzzy={record['has_fuzzy']} but "
            f"DSL {'contains' if actual_fuzzy else 'does not contain'} FUZZY"
        )

    # non-empty input
    if not record.get("input", "").strip():
        return False, "input is empty"

    # dsl validation
    ok, reason = validate_dsl(record.get("output", ""))
    if not ok:
        return False, f"DSL error — {reason}"

    return True, "ok"


# ---------------------------------------------------------------------------
# Dataset-level validation
# ---------------------------------------------------------------------------

def validate_dataset(records: list[dict]) -> list[ValidationError]:
    """
    Validate a list of records. Returns a list of ValidationError objects.
    An empty list means all records are valid.
    """
    errors: list[ValidationError] = []

    for record in records:
        record_id = record.get("id", "<no-id>")
        ok, reason = validate_record(record)
        if not ok:
            snippet = (record.get("output", "") or "")[:80]
            errors.append(ValidationError(
                record_id = record_id,
                reason    = reason,
                field     = "record",
                snippet   = snippet if snippet else None,
            ))

    return errors


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def print_validation_report(errors: list[ValidationError], max_show: int = 10) -> None:
    """Print a human-readable validation report to stdout."""
    if not errors:
        print("[VALID] 0 errors — all records passed validation")
        return

    print(f"[INVALID] {len(errors)} error(s) found:")
    for err in errors[:max_show]:
        print(f"  ✗ {err.record_id}: {err.reason}")
        if err.snippet:
            print(f"      snippet: {err.snippet!r}")

    if len(errors) > max_show:
        print(f"  ... and {len(errors) - max_show} more")