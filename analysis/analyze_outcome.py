"""
Final outcome evaluation - ties victim side and scammer side analyses together.

Three parts:
1.  Descriptive summary: how conversations actually ended, alongside max engagement
    reached - a clean final result table.
2.  Does the scammer's retreat rate correlate with how far the victim engaged?
    Spearman Correlation - appropriate here since these are ordinal/skewed,
    not assumed normal continuous variables.
3.  Does tactic usage volume correlate with engagement outcome, per tactic?

Reuses the 2 metric CSVs from analyze_victim.py and analyze_scammer.py

CAVEAT:
Correlation does not establish that retreating causes better engagement.
Personas that engage more may also naturally produce more opportunities 
for the scammer to detect suspicion and retreat, in either causal direction,
or both could be driven by the persona's traits underneath.
"""

import json
import pandas as pd
from scipy.stats import spearmanr

RELABELED_FILE = "conversation_relabeled_full.json"
TACTICS = ["authority", "urgency", "trust_building", "fear_induction"]

def descriptive_summary():
    with open(RELABELED_FILE) as f:
        conversations=json.load(f)

    ended_reasons = pd.Series([c.get("ended_reason") for c in conversations]).value_counts()
    total_turns = pd.Series([c.get("total_turns") for c in conversations])

    print("How conversations ended (n=60)")
    print(ended_reasons)
    print(f"\nMean total turns: {total_turns.mean():.1f}, median: {total_turns.median():.0f}")

def merged_metrics():
    victim = pd.read_csv("victim_conversation_metrics.csv")
    scammer = pd.read_csv("scammer_conversation_metrics.csv")
    merged = victim.merge(
        scammer[["persona_uuid", "run_number", "retreat_rate", "retreat_count"] + [f"{t}_count" for t in TACTICS]],
        on=["persona_uuid", "run_number"],
    )
    merged.to_csv("outcome_merged_metrics.csv", index=False)
    return merged

def correlation_analysis(merged):
    print("\nDoes retreat rate correlate with max engagement reached?")
    rho, p = spearmanr(merged["retreat_rate"], merged["max_engagement"])
    print(f"    Spearman rho = {rho:.3f}, p = {p:.4f}")

    print("\nDoes tactic usage volume correlate with max engagement reached?")
    for tactic in TACTICS:
        rho, p = spearmanr(merged[f"{tactic}_count"], merged["max_engagement"])
        print(f"    {tactic}: rho = {rho:.3f}, p = {p:.4f}")

def main():
    descriptive_summary()
    merged = merged_metrics()
    print(f"\nMerged metrics for {len(merged)} conversations, saved to 'outcome_merged_metrics.csv'")
    correlation_analysis(merged)

if __name__ == "__main__":
    main()