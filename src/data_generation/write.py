"""
writer.py
=========
All I/O for the dataset pipeline.

Responsibilities:
  - Write records to JSONL files
  - Split a flat list into train / val / test
  - Compute file checksums (for dataset versioning)
  - Compute and write dataset statistics

Public API
----------
  write_jsonl(path, records)
  read_jsonl(path)           → list[dict]
  split_records(records)     → dict[str, list[dict]]
  write_splits(base_dir, records)
  compute_stats(named_paths) → dict
  write_stats(named_paths, stats_path)
  print_summary(stats)
"""

import hashlib
import json
from collections import defaultdict
from pathlib import Path

from configs.data_config import SPLIT_RATIOS


# ---------------------------------------------------------------------------
# Read / write
# ---------------------------------------------------------------------------

def write_jsonl(path: Path, records: list[dict]) -> None:
    """
    Write records to a JSONL file. Creates parent directories if needed.
    Each record is written as a single JSON line.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"  [wrote] {len(records):>5} records  →  {path}")


def read_jsonl(path: Path) -> list[dict]:
    """
    Read records from a JSONL file.
    Skips blank lines silently.
    """
    if not path.exists():
        return []
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


# ---------------------------------------------------------------------------
# Splitting
# ---------------------------------------------------------------------------

def split_records(
    records: list[dict],
    ratios: dict[str, float] | None = None,
) -> dict[str, list[dict]]:
    """
    Split a list of records into train / val / test subsets.

    Records should already be shuffled before calling this.
    Ratios must sum to 1.0 (tolerance: 0.001).

    Returns a dict: {"train": [...], "val": [...], "test": [...]}
    """
    ratios = ratios or SPLIT_RATIOS
    total  = sum(ratios.values())
    if abs(total - 1.0) > 0.001:
        raise ValueError(f"Split ratios must sum to 1.0, got {total}")

    n       = len(records)
    splits  = {}
    cursor  = 0

    keys    = list(ratios.keys())
    for i, key in enumerate(keys):
        if i == len(keys) - 1:
            # Last split gets the remainder to avoid rounding gaps
            splits[key] = records[cursor:]
        else:
            end          = cursor + int(n * ratios[key])
            splits[key]  = records[cursor:end]
            cursor       = end

    return splits


def write_splits(base_dir: Path, records: list[dict]) -> dict[str, Path]:
    """
    Split records and write each split to base_dir/<split>.jsonl.

    Returns a dict of split name → file path.
    """
    splits = split_records(records)
    paths  = {}
    for split_name, split_records_ in splits.items():
        path           = base_dir / f"{split_name}.jsonl"
        write_jsonl(path, split_records_)
        paths[split_name] = path
    return paths


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def compute_stats(named_paths: dict[str, Path]) -> dict:
    """
    Compute statistics for a set of named JSONL files.

    named_paths: {"gold": Path(...), "train": Path(...), ...}

    Returns a dict suitable for JSON serialisation.
    """
    stats = {}
    for name, path in named_paths.items():
        if not path.exists():
            continue
        records = read_jsonl(path)

        intent_counts: dict[str, int] = defaultdict(int)
        source_counts: dict[str, int] = defaultdict(int)
        fuzzy_count = 0

        for r in records:
            intent_counts[r.get("intent", "UNKNOWN")] += 1
            source_counts[r.get("source", "unknown")]  += 1
            if r.get("has_fuzzy"):
                fuzzy_count += 1

        stats[name] = {
            "count":         len(records),
            "fuzzy_count":   fuzzy_count,
            "intent_counts": dict(sorted(intent_counts.items())),
            "source_counts": dict(sorted(source_counts.items())),
            "checksum_md5":  _file_checksum(path),
            "path":          str(path),
        }
    return stats


def write_stats(named_paths: dict[str, Path], stats_path: Path) -> dict:
    """Compute stats, write to JSON, and return the stats dict."""
    stats = compute_stats(named_paths)
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    stats_path.write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    print(f"\n  [stats] Written → {stats_path}")
    return stats


def print_summary(stats: dict) -> None:
    """Print a compact summary table to stdout."""
    print("\n── Dataset Summary " + "─" * 45)
    header = f"  {'split':<10} {'records':>7}  {'fuzzy':>5}  {'checksum':>10}"
    print(header)
    print("  " + "─" * (len(header) - 2))
    for name, s in stats.items():
        chk = s.get("checksum_md5", "")[:8]
        print(
            f"  {name:<10} {s['count']:>7}  "
            f"{s['fuzzy_count']:>5}  {chk:>10}"
        )
    print()


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _file_checksum(path: Path) -> str:
    """MD5 checksum of a file — used for dataset versioning."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()