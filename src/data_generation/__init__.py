"""
src.data_generation
===================
Dataset pipeline for IntentCompiler.

Submodules
----------
data_config   — constants, vocab banks, paths
dsl_builder   — canonical DSL string construction
gold          — hand-authored gold evaluation dataset
synthetic     — template-based synthetic generation
paraphrase    — LLM-powered paraphrase augmentation (uses utils.LLMHelper)
validator     — DSL structural + record validation
write         — JSONL I/O, train/val/test splitting, stats

Note: LLMHelper and config loading live in utils.llm_helper, not here.
"""

from configs.data_config import (
    ROOT_DIR,
    GOLD_DIR,
    SYNTHETIC_DIR,
    OOD_DIR,
    STATS_FILE,
    SPLIT_RATIOS,
    RANDOM_SEED,
    SYNTHETIC_PER_TEMPLATE,
)
from src.data_generation.dsl_builder import (
    dsl,
    fuzzy,
    rename_dsl,
    has_fuzzy,
    extract_intent,
)
from src.data_generation.gold import generate_gold
from src.data_generation.synthetic import generate_synthetic, TEMPLATES
from src.data_generation.paraphrase import paraphrase_dataset
from src.data_generation.validator import (
    validate_dsl,
    validate_record,
    validate_dataset,
    print_validation_report,
    ValidationError,
)
from src.data_generation.write import (
    write_jsonl,
    read_jsonl,
    split_records,
    write_splits,
    compute_stats,
    write_stats,
    print_summary,
)

__all__ = [
    # data_config
    "ROOT_DIR", "GOLD_DIR", "SYNTHETIC_DIR", "OOD_DIR", "STATS_FILE",
    "SPLIT_RATIOS", "RANDOM_SEED", "SYNTHETIC_PER_TEMPLATE",
    # dsl_builder
    "dsl", "fuzzy", "rename_dsl", "has_fuzzy", "extract_intent",
    # gold
    "generate_gold",
    # synthetic
    "generate_synthetic", "TEMPLATES",
    # paraphrase
    "paraphrase_dataset",
    # validator
    "validate_dsl", "validate_record", "validate_dataset",
    "print_validation_report", "ValidationError",
    # write
    "write_jsonl", "read_jsonl", "split_records", "write_splits",
    "compute_stats", "write_stats", "print_summary",
]
