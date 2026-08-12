#!/usr/bin/env python3
"""CONFIRMATORY-tier external-LLM comparator (frozen scale-up of the dev run).
Same frozen 3-condition design (DIRECT/FREE_COT/RAKL_GATE) as
research/llm_comparator_dev_v1/run_comparator.py, scaled to n_per_cell=14
(~504 tasks, ~448 decidable >= Paper II's n~431 target), fresh seed 20260812.
Reuses the frozen prompts/parser/scoring; only SEED, N_PER_CELL, OUT change."""
import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"llm_comparator_dev_v1"))
import run_comparator as R
R.SEED=20260812
R.N_PER_CELL=14
R.OUT=Path(__file__).resolve().parent
R.main()
