"""
paraphrase.py
=============
LLM-powered paraphrase augmentation for the synthetic dataset.

Uses ``infrakit.llm.LLMClient.batch_generate`` for multithreaded async
requests, chunking multiple sentences into a single macro-prompt to save API limits.

Public API
----------
  paraphrase_dataset(records, client, provider, n, skip_fuzzy, chunk_size)  → list[dict]
"""

from __future__ import annotations

import sys
import json
from pydantic import BaseModel
from infrakit.llm import LLMClient, Prompt

from src.data_generation.validator import validate_record


class ParaphraseItem(BaseModel):
    id: str
    paraphrases: list[str]

class ParaphraseBatchResult(BaseModel):
    """Structured response expected from the LLM paraphraser when batching."""
    items: list[ParaphraseItem]


_SYSTEM_PROMPT = """\
You are a dataset augmentation assistant for a command-compiler AI.

Your task: you will be given a JSON array of records, each containing an "id" and "text" (a natural-language command). 
For EACH record, produce exactly {n} distinct rephrasings that all express the SAME intent. The paraphrases should:

- Vary vocabulary, sentence structure, and phrasing naturally
- Sound like real user utterances (casual, terse, or verbose)
- Occasionally include natural human typos (e.g., dropped punctuation, transposed letters, or missing spaces)
- NOT change the meaning, target files, or operation
- NOT include any DSL, code, or structured output — plain English only
- NOT repeat the original sentence verbatim

Respond ONLY with a valid JSON object matching exactly this schema:
{{
  "items": [
    {{
      "id": "<id_from_input>",
      "paraphrases": ["<phrase1>", "<phrase2>", ...]
    }}
  ]
}}

No explanation, no markdown fences, no extra keys. Only the JSON object.\
"""


def paraphrase_dataset(
    records: list[dict],
    client: LLMClient,
    provider: str = "gemini",
    n: int = 4,
    skip_fuzzy: bool = False,
    chunk_size: int = 20,
) -> list[dict]:
    """
    Paraphrase a list of dataset records, grouping multiple records into single macro-prompts.

    Parameters
    ----------
    records:
        Source records to augment.
    client:
        Configured ``infrakit.llm.LLMClient``.
    provider:
        The provider to use, usually "gemini".
    n:
        Number of paraphrases per record.
    skip_fuzzy:
        If True, skip records whose DSL contains FUZZY placeholders.
    chunk_size:
        Number of sentences to pack into a single LLM prompt.
    """
    valid_records = []
    
    for record in records:
        if skip_fuzzy and record.get("has_fuzzy"):
            continue
        valid_records.append(record)

    if not valid_records:
        return []

    # Group into macro-chunks
    prompts = []
    chunk_map = [] # Maps prompt index back to the valid_records slice
    
    for i in range(0, len(valid_records), chunk_size):
        chunk = valid_records[i : i + chunk_size]
        chunk_map.append(chunk)
        
        # Prepare the payload for the prompt
        payload = [{"id": r["id"], "text": r["input"]} for r in chunk]
        
        prompts.append(Prompt(
            system=_SYSTEM_PROMPT.format(n=n),
            user=json.dumps(payload, indent=2)
        ))

    print(f"\n  [batch] Grouped {len(valid_records)} records into {len(prompts)} macro-prompts (chunk_size={chunk_size})")
    batch_result = client.batch_generate(
        prompts=prompts,
        provider=provider,
        response_model=ParaphraseBatchResult,
    )

    all_paraphrases: list[dict] = []
    failed_prompts = 0
    failed_items = 0

    for chunk_idx, result in enumerate(batch_result.results):
        source_chunk = chunk_map[chunk_idx]
        source_dict = {r["id"]: r for r in source_chunk}
        
        if result.error or not result.schema_matched or not result.parsed:
            failed_prompts += 1
            print(f"  [llm-error] macro-prompt error: {result.error}", file=sys.stderr)
            continue
        
        for item in result.parsed.items:
            orig_record = source_dict.get(item.id)
            if not orig_record:
                print(f"  [llm-error] LLM hallucinated id: {item.id}", file=sys.stderr)
                continue
                
            phrases = [p.strip() for p in item.paraphrases if p.strip()]
            if not phrases:
                failed_items += 1
                continue
                
            for i, phrase in enumerate(phrases[:n], start=1):
                new_record = {
                    **orig_record,
                    "id": f"{orig_record['id']}_p{i}",
                    "input": phrase,
                    "source": "paraphrase",
                }
                ok, reason = validate_record(new_record)
                if not ok:
                    print(f"  [invalid-para] {new_record['id']}: {reason}", file=sys.stderr)
                    continue
                all_paraphrases.append(new_record)

    print(
        f"  [batch complete] Generated {len(all_paraphrases)} paraphrases. "
        f"Prompt Success: {batch_result.success_count} / Failed: {batch_result.failure_count + failed_prompts}"
    )
    print(f"  [tokens] Total used: {batch_result.total_tokens}")

    return all_paraphrases
