"""
utils/llm_helper.py
===================
Shared LLM setup for the IntentCompiler pipeline.

Reads Gemini API keys and model settings from ``configs/llm_config.yaml``,
cross-references rate limits from ``utils/gemini_models.json``, and
returns a configured ``infrakit.llm.LLMClient`` which handles quota
tracking, rate limiting, and batch processing natively.
"""

import os
import json
from pathlib import Path
from typing import Optional

from infrakit.llm import LLMClient, QuotaConfig

from configs.config import APP_CONFIG, get_gemini_api_keys

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_UTILS_DIR        = Path(__file__).parent
_PROJECT_ROOT     = _UTILS_DIR.parent
_DEFAULT_CONFIG   = _PROJECT_ROOT / "configs" / "llm_config.yaml"
_GEMINI_MODELS    = _UTILS_DIR / "gemini_models.json"


def _load_gemini_registry() -> dict:
    if not _GEMINI_MODELS.exists():
        raise FileNotFoundError(
            f"Gemini model registry not found: {_GEMINI_MODELS}"
        )
    return json.loads(_GEMINI_MODELS.read_text(encoding="utf-8"))


def list_models() -> None:
    registry = _load_gemini_registry()
    print("\n-- Available Gemini Models ---------------------------------")
    for model_id, info in registry["models"].items():
        ft = info["free_tier"]
        print(
            f"  {model_id:<30}  "
            f"RPM={ft['rpm']:<4}  RPD={ft['rpd']:<6}  "
            f"TPM={ft['tpm']:>10,}  [{info['status']}]"
        )
    print(f"\n  Recommended for paraphrase : {registry['recommended_for_paraphrase']}")
    print(f"  Recommended for quality    : {registry['recommended_for_quality_check']}\n")


def setup_llm_client() -> tuple[LLMClient, str, int, int]:
    """
    Builds and returns an infrakit LLMClient with properly configured
    quotas for each key, based on our models registry.

    Returns:
        (client, model_name, n_per_record, chunk_size)
    """
    llm_cfg  = APP_CONFIG.get("llm", {})
    para_cfg = APP_CONFIG.get("paraphrase", {})

    gemini_keys = get_gemini_api_keys()
    if not gemini_keys:
        raise ValueError("No valid Gemini API keys found in .env. Populate GEMINI_API_KEYS.")

    model       = llm_cfg.get("model", "gemini-3.1-flash-lite")
    storage_dir = llm_cfg.get("storage_dir", "./logs/llm_state")
    n_default   = int(para_cfg.get("n_per_record", 4))
    chunk_size  = int(para_cfg.get("chunk_size", 20))

    registry = _load_gemini_registry()
    known_models = registry.get("models", {})
    if model not in known_models:
        raise ValueError(f"Unknown model: '{model}'. Available: {', '.join(known_models.keys())}")

    free_limits = known_models[model].get("free_tier", {})

    # infrakit LLMClient natively handles async batches and quotas
    client = LLMClient(
        keys={"gemini_keys": gemini_keys},
        storage_dir=storage_dir,
        gemini_model=model,
    )

    for key in gemini_keys:
        key_id = key[:8]
        try:
            client.set_quota(
                provider="gemini",
                key_id=key_id,
                quota=QuotaConfig(
                    rpm_limit=free_limits.get("rpm"),
                    tpm_limit=free_limits.get("tpm"),
                    daily_token_limit=None,
                    reset_hour_utc=free_limits.get("reset_hour_utc", 7),
                ),
            )
        except Exception:
            pass  # infrakit might not have state for new key yet, safe to ignore

    return client, model, n_default, chunk_size
