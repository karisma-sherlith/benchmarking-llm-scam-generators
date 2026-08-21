# Benchmarking LLMs as Scam Generators — Project Archive

Supporting code, data, and documentation for the MSc dissertation
*"Benchmarking LLMs as Scam Generators: Persona-Conditioned Victim
Susceptibility in Synthetic Conversations"* (University of Edinburgh,
School of Informatics, 2026). Also available at:
https://github.com/karisma-sherlith/benchmarking-llm-scam-generators

## Data provenance

- **DarkGram** (`data/darkgram_threads.csv` and derived files): reconstructed
  from the DarkGram dataset of Telegram cybercriminal activity channels,
  originally released by Roy et al. (2024), *"DarkGram: A Large-Scale
  Analysis of Cybercriminal Activity Channels on Telegram,"* USENIX Security
  2024. The original raw dataset is not included in this archive (large,
  publicly available from the original authors); this archive contains only
  the derived, project-specific outputs (reconstructed threads, translations,
  classifications).
- **Personas** (`persona_sample_12.csv`): sampled from Nemotron-Personas-USA
  (Extended), NVIDIA, accessed via the NGC catalogue. The full 1.24GB raw
  persona dataset is not included; only the 12 sampled persona profiles used
  in this project are retained.
- **Synthetic conversations** (`conversation_*.json` files): generated
  entirely by this project (Phase 2), not sourced externally. No real
  individuals or real scam interactions are involved.

## Directory structure

### `data/` — Phase 1: Dataset construction
- `explore_darkgram.py` — initial exploration of DarkGram category/channel
  counts.
- `sample_darkgram.py` — sample message content inspection across
  categories.
- `extract_darkgram_threads.py` — reconstructs multi-turn conversation
  threads from raw posts + replies. Produces `darkgram_threads.csv`.
- `translate_darkgram.py` — detects non-English content (script-regex +
  Romanised Hindi heuristic) and translates flagged replies via GPT-4.1-mini
  (ELM API). Produces `darkgram_translated.csv`.
- `classify_scam_darkgram.py` — two-stage LLM classification pipeline
  labelling each thread scam / potential_scam / illicit_not_scam / unclear,
  with manipulation-tactic tagging. Produces `darkgram_scam_classified.csv`
  and `darkgram_scam_and_potential_scam.csv`.
- `annotate_darkgram_threads.py` — manual annotation support script.
  Produces `darkgram_threads_annotated.csv`.
- `analyse_distribution.py` — dataset distribution statistics (thread
  counts, reply-length distribution, language breakdown).
- `phase1_negative_class_validation_sample.xlsx` — stratified manual
  validation sample used to estimate the classification false-negative
  rate (Section 3.3 of the dissertation).

### `generation/` — Phase 2: Synthetic conversation generation
- `sample_personas.py` — factorial sampling script (2 sexes × 3 age
  brackets × 2 agreeableness levels) over the Nemotron-Personas-USA
  Extended dataset. Produces `persona_sample_12.csv`.
- `explore_persona.py` — persona field inspection/validation.
- `prompts.py` — scammer and victim system prompt templates (reproduced in
  Appendix A of the dissertation).
- `conversation_loop.py` — the staged-visibility, turn-by-turn
  scammer/victim conversation generation loop. Produces the
  `conversation_*.json` files (test batches and full batch).

### `annotation/` — Phase 3: Evaluation and relabelling
- `persona_distinctiveness_check.py` — decision-tree leave-one-out
  validation of persona distinguishability by agreeableness.
- `relabel_victim.py` / `relabel_scammer.py` — LLM-based (GPT-4.1-mini via
  ELM API) turn-level relabelling, applying the rubrics in `docs/`.
  Produce `conversation_relabeled_victim.json` /
  `conversation_relabeled_full.json`.
- `sampling_victim_relabel.py` / `sampling_scammer_relabel.py` — draw
  stratified blind-review samples for inter-rater validation. Produce the
  `*_validation_blind_review.json` (to fill manually) and
  `*_validation_answer_key.json` (ground truth) file pairs.

### `analysis/` — Statistical analysis and figures
- `analyze_victim.py` / `analyze_scammer.py` / `analyze_outcome.py` —
  survival analysis, Mann-Whitney/Kruskal-Wallis, chi-square, and Spearman
  correlation analyses. Produce `victim_conversation_metrics.csv`,
  `scammer_conversation_metrics.csv`, `outcome_merged_metrics.csv`.
- `plot_victim.py` / `plot_scammer.py` — generate
  `victim_suspicion_survival_curved.png` and
  `retreat_trigger_distribution.png`.

### `docs/`
- `VICTIM SIDE EVALUATION RUBRIC.md` / `SCAMMER SIDE EVALUATION RUBRIC.md`
  — full annotation rubrics used by `annotation/relabel_*.py` (reproduced
  in Appendix C of the dissertation).
- `Darkgram Dataset.docx`, `PERSONA DISTINCTIVENESS CHECK OUTPUT.md`,
  `CONV GENERATION - TEST BATCH FINDINGS.md`,
  `CONV GENERATION FULL BATCH RESULTS.md`, `PHASE 3 FINDINGS.md` —
  intermediate findings notes generated during the project, corresponding
  to the results reported in the dissertation.

## Reproducing the pipeline

Scripts are intended to be run in the following order. Each stage's output
CSV/JSON is provided in this archive, so any stage can also be inspected
directly without rerunning earlier stages.

1. `data/extract_darkgram_threads.py`
2. `data/translate_darkgram.py`
3. `data/classify_scam_darkgram.py`
4. `generation/sample_personas.py`
5. `annotation/persona_distinctiveness_check.py`
6. `generation/conversation_loop.py`
7. `annotation/relabel_victim.py` and `annotation/relabel_scammer.py`
8. `analysis/analyze_victim.py`, `analysis/analyze_scammer.py`,
   `analysis/analyze_outcome.py`
9. `analysis/plot_victim.py`, `analysis/plot_scammer.py`

## Requirements

- Python 3.x, with dependencies listed in `requirements.txt` (or: pandas,
  openai, python-dotenv, scipy, lifelines, matplotlib).
- API access to an OpenAI-compatible endpoint (GPT-4.1-mini used
  throughout via the University of Edinburgh ELM API).
- API keys are read from a local `.env` file (`ELM_API_KEY=...`), which is
  **not included** in this archive for security reasons. A working key
  must be supplied to rerun any script making API calls; all provided
  output files can be inspected without one.

## Notes on archive contents

- `venv/` and `__pycache__/` are excluded from this archive; dependencies
  are listed above and can be installed via `pip install -r
  requirements.txt`.
- The raw, unprocessed DarkGram dataset and the full raw Nemotron-Personas
  dataset are not included (large, publicly available from their original
  sources, cited above); only this project's derived outputs are retained.
- No `.env` file or API credentials are included in this archive.