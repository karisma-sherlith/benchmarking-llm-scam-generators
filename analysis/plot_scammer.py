"""
Grouped bar chart: suspicion level distribution immediately preceding
a scammer retreat vs. the baseline distribution across all the victim turns.
Visual plot for the most novel finding (p<0.0001) - oscillation pattern observed earlier.
"""

import json
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RELABELED_FILE = "conversation_relabeled_full.json"

def get_retreat_trigger_distributions():
    with open(RELABELED_FILE) as f:
        conversations = json.load(f)

    retreat_preceding_suspicion = []
    all_victim_suspicion = []

    for conv in conversations:
        transcript = conv["transcript"]
        for i, turn in enumerate(transcript):
            if turn.get("speaker") == "victim":
                all_victim_suspicion.append(turn.get("relabel_suspicion"))
            if turn.get("speaker") == "scammer" and turn.get("relabel_retreat"):
                if i> 0  and transcript[i-1].get("speaker") == "victim":
                    retreat_preceding_suspicion.append(transcript[i-1].get("relabel_suspicion"))

    retreat_props = pd.Series(retreat_preceding_suspicion).value_counts(normalize=True)
    baseline_props = pd.Series(all_victim_suspicion).value_counts(normalize=True)

    return retreat_props, baseline_props

def main():
    retreat_props, baseline_props = get_retreat_trigger_distributions()

    categories = ["none", "mild", "high"]
    retreat_vals = [retreat_props.get(c, 0) for c in categories]
    baseline_vals = [baseline_props.get(c, 0) for c in categories]

    x = range(len(categories))
    width = 0.35

    fig, ax = plt.subplots(figsize=(7,5))
    ax.bar([i-width/2 for i in x], baseline_vals, width, label="Baseline (all victim turns)", color="#4C72B0")
    ax.bar([i+width/2 for i in x], retreat_vals, width, label="Immediately before a scammer retreat", color="#C44E52")

    ax.set_xticks(list(x))
    ax.set_xticklabels(categories)
    ax.set_ylabel("Proportion of turns")
    ax.set_title("Victim suspicion level: baseline vs. immediately preceding a scammer retreat")
    ax.legend()

    plt.tight_layout()
    plt.savefig("retreat_trigger_distribution.png", dpi=150)
    print("Saved 'retreat_trigger_distribution.png'")

if __name__ == "__main__":
    main()