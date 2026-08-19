# Benchmarking LLMs as Scam Generators

Code and data for the MSc dissertation *"Benchmarking LLMs as Scam Generators:
Persona-Conditioned Victim Susceptibility in Synthetic Conversations"*
(University of Edinburgh, School of Informatics, 2026).

This project benchmarks LLMs' capability to generate multi-turn scam
conversations, and tests whether that behaviour, and a simulated victim's
susceptibility, varies systematically with victim persona traits (sex, age,
agreeableness). It combines a real-world dataset (DarkGram, Telegram
cybercriminal channels) with a persona-conditioned synthetic conversation
generation pipeline, evaluated through an inter-rater-validated turn-level
annotation scheme and statistical analysis.

## Repository structure

- `data/` — Phase 1: DarkGram thread reconstruction, language detection,
  translation, and scam classification pipeline.
- `generation/` — Phase 2: persona sampling, persona distinctiveness
  validation, and the staged-visibility scammer/victim conversation
  generation loop.
- `annotation/` — Phase 3: turn-level relabelling scripts (victim- and
  scammer-side) and blind-review validation.
- `analysis/` — Statistical analysis (survival analysis, Mann-Whitney,
  Kruskal-Wallis, Spearman correlation) and figure generation.
- `docs/` — Evaluation rubrics and supporting documentation.

## Summary of findings

Across 60 synthetic scammer/victim conversations, victim agreeableness
significantly affected suspicion escalation (log-rank p < 0.0001) and
scammer retreat behaviour (p = 0.029), while sex showed no significant
effect. No conversation resulted in explicit financial compliance. Full
methodology and results are reported in the dissertation.

## Requirements

Python 3.x, `python-dotenv`, API access to an OpenAI-compatible endpoint
(GPT-4.1-mini used throughout). API keys are read from a local `.env` file
(not committed).
