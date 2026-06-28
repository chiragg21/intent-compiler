"""
scripts/run_pipeline.py
=======================
Unified orchestrator for IntentCompiler dataset generation.

Usage
-----
  # Run the full pipeline
  uv run python scripts/run_pipeline.py --steps all

  # Run specific steps
  uv run python scripts/run_pipeline.py --steps gold synthetic
  uv run python scripts/run_pipeline.py --steps paraphrase --limit 500
"""

import argparse
import sys
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from configs.data_config import GOLD_DIR, SYNTHETIC_DIR, STATS_FILE, SYNTHETIC_PER_TEMPLATE
from src.data_generation.gold import generate_gold
from src.data_generation.synthetic import generate_synthetic, TEMPLATES
from src.data_generation.paraphrase import paraphrase_dataset
from src.data_generation.validator import validate_dataset, print_validation_report
from src.data_generation.write import write_jsonl, read_jsonl, write_splits, write_stats, print_summary
from utils.llm_helper import setup_llm_client, list_models


def run_gold() -> bool:
    print("\n== [1] Gold Dataset Generation ==================================\n")
    records = generate_gold()
    
    errors = validate_dataset(records)
    if errors:
        print_validation_report(errors)
        print("  ✗ Aborting — Fix validation errors in gold.py.", file=sys.stderr)
        return False
        
    gold_path = GOLD_DIR / "gold.jsonl"
    write_jsonl(gold_path, records)
    stats = write_stats({"gold": gold_path}, STATS_FILE)
    print_summary(stats)
    return True


def run_synthetic(n_per_template: int) -> bool:
    print("\n== [2] Synthetic Dataset Generation ============================\n")
    records = generate_synthetic(n_per_template=n_per_template)
    
    errors = validate_dataset(records)
    if errors:
        print_validation_report(errors)
        print("  ✗ Aborting — Fix validation errors in synthetic.py.", file=sys.stderr)
        return False
        
    split_paths = write_splits(SYNTHETIC_DIR, records)
    stats = write_stats({f"synthetic_{k}": v for k, v in split_paths.items()}, STATS_FILE)
    print_summary(stats)
    return True


def run_paraphrase(limit: int | None = None, skip_fuzzy: bool = False, batch_save_every: int = 100) -> bool:
    print("\n== [3] Paraphrase Augmentation ==================================\n")
    train_path = SYNTHETIC_DIR / "train.jsonl"
    if not train_path.exists():
        print(f"  ✗ {train_path} not found. Run synthetic step first.", file=sys.stderr)
        return False
        
    records = read_jsonl(train_path)
    if limit:
        records = records[:limit]
        print(f"  Limited to {limit} records.")
        
    out_para_path = SYNTHETIC_DIR / "train_para.jsonl"
    out_aug_path = SYNTHETIC_DIR / "train_augmented.jsonl"

    # --- CHECKPOINTING ---
    processed_base_ids = set()
    all_para = []
    
    if out_para_path.exists():
        try:
            existing_paras = read_jsonl(out_para_path)
            for r in existing_paras:
                # "id": "originalId_p1" -> extract "originalId"
                base_id = r["id"].rsplit("_p", 1)[0]
                processed_base_ids.add(base_id)
            all_para.extend(existing_paras)
            print(f"  [checkpoint] Resuming from {len(existing_paras)} existing paraphrases.")
            print(f"  [checkpoint] {len(processed_base_ids)} original records already processed.")
        except Exception as e:
            print(f"  ⚠ Failed to read existing {out_para_path}: {e}")

    remaining_records = [r for r in records if r["id"] not in processed_base_ids]
    print(f"  [checkpoint] {len(remaining_records)} records remaining to process.\n")
        
    if remaining_records:
        try:
            client, model, n_per_record, chunk_size = setup_llm_client()
        except Exception as e:
            print(f"  ✗ Setup Failed: {e}", file=sys.stderr)
            return False
            
        # Process in chunks and append incrementally to out_para_path
        with open(out_para_path, "a" if processed_base_ids else "w", encoding="utf-8") as f:
            for start_idx in range(0, len(remaining_records), batch_save_every):
                chunk = remaining_records[start_idx : start_idx + batch_save_every]
                print(f"\n  ── Processing chunk [{start_idx} : {start_idx + len(chunk)}] of {len(remaining_records)} ──")
                
                chunk_paras = paraphrase_dataset(
                    chunk, 
                    client=client, 
                    provider="gemini", 
                    n=n_per_record, 
                    skip_fuzzy=skip_fuzzy,
                    chunk_size=chunk_size
                )
                
                # Validation is already done in paraphrase_dataset, but double check
                errors = validate_dataset(chunk_paras)
                if errors:
                    print_validation_report(errors)
                    print("  ⚠ Invalid paraphrase records removed.", file=sys.stderr)
                    invalid_ids = {e.record_id for e in errors}
                    chunk_paras = [r for r in chunk_paras if r["id"] not in invalid_ids]

                for record in chunk_paras:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()
                
                all_para.extend(chunk_paras)
    
    print("\n  [5/5] Merging originals + paraphrases …")
    merged = records + all_para
    write_jsonl(out_aug_path, merged)
    
    stats = write_stats({"synthetic_train_para": out_para_path, "synthetic_train_augmented": out_aug_path}, STATS_FILE)
    print_summary(stats)
    return True


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--steps", nargs="+", choices=["all", "gold", "synthetic", "paraphrase"], default=["all"])
    p.add_argument("--n-synthetic", type=int, default=SYNTHETIC_PER_TEMPLATE)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--skip-fuzzy", action="store_true")
    p.add_argument("--list-models", action="store_true")
    p.add_argument("--batch-save-every", type=int, default=100)
    
    args = p.parse_args()
    
    if args.list_models:
        list_models()
        return 0
        
    steps = ["gold", "synthetic", "paraphrase"] if "all" in args.steps else args.steps
    
    if "gold" in steps:
        if not run_gold(): return 1
    if "synthetic" in steps:
        if not run_synthetic(args.n_synthetic): return 1
    if "paraphrase" in steps:
        if not run_paraphrase(args.limit, args.skip_fuzzy, args.batch_save_every): return 1
        
    print("\n  ✓ Pipeline complete.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
