# Intent Compiler

A data pipeline for training a model that compiles natural-language file-management commands ("move my resume to Job", "clean up old logs older than 30 days") into a canonical, executable DSL.

## What it does

Rather than hand-writing a parser for every phrasing of a file operation, this project builds the *dataset* a model would need to learn the mapping: natural language in, a structured DSL call out (`MOVE(src=..., dst=..., ext=...)`, `RENAME(...)`, `CLEAN(...)`, etc.), including ambiguous "fuzzy" references a real user would type ("copy my resume" rather than a literal path).

The pipeline produces three splits:

- **Gold** (`src/data_generation/gold.py`) — hand-authored examples, never auto-generated, used only for evaluation and never for training.
- **Synthetic** (`src/data_generation/synthetic.py`) — template-based generation: each template pairs an NL pattern with a DSL-building function and a random-variable generator, covering standard OS folders, personal folder names, fuzzy file/folder references, and mixed cases.
- **Paraphrase** (`src/data_generation/paraphrase.py`) — LLM-based paraphrasing of the synthetic examples to widen phrasing coverage beyond the fixed templates.

A `dsl_builder.py` module with zero internal dependencies defines the canonical DSL grammar (quoting rules, `FUZZY(...)` placeholders, `RENAME`'s special-cased `from`/`to` params) so every other module builds DSL strings the same way.

## Scope covered

The vocabulary bank (`configs/data_config.py`) currently covers file operations (move/copy/rename/clean/search/compress), git commands, process management, and app launching — all driven from one config file so new folder names, fuzzy references, or vocab can be added without touching pipeline code.

## Stack

- Python 3.13, managed with `uv`
- Google Gemini (`google-genai`) for paraphrase generation
- [`infrakit`](https://github.com/chiragg21/Infrakit) (this author's own toolkit) for the underlying LLM client

## Status

Early-stage: the data-generation pipeline (DSL grammar, synthetic templates, gold set, paraphrasing, validation) is built; the compiler model itself (training/inference on top of this data) is not yet implemented. `main.py` is currently a placeholder entry point.

## Getting started

```bash
uv sync
uv run main.py
```
