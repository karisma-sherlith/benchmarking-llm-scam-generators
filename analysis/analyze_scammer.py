"""
Scammer side final analysis, built on the validated (kappa-checked)
phase/pressure/tactic labels from relabel_scammer.py

Four Analyses:
1.  Time to first closure attempt by persona trait
    (Survival analysis, same reasoning as victim-side - 
    some conversations never reach it - censored).
2.  Retreat frequency by persona trait (Mann-Whitnet/Kruskal-Wallis)
3.  Tactic usage counts by persona trait, for each of the 4 tactics.
4.  Retreat Trigger Analysis - direct test of the oscillation pattern noticed.
    For every scammer turn flagged as a retreat, what was the victim's suspicion level on the 
    immediately preceding victim turn? Compared against the baseline distribution of suspicion
    across all victim turns, via chi-square - if retreats are disproportionately preceded
    by "high" suspicion turns compared to the baseline rate, that's real statistical support
    for the pattern noticed earlier through skimming.
"""

import json
import pandas as pd
from scipy.stats import mannwhitneyu, kruskal, chi2_contingency
from lifelines import KaplanMeierFitter
from lifelines.statistics import logrank_test, multivariate_logrank_test
import ast

RELABELED_FILE = "conversation_relabeled_full.json"
PERSONA_FILE = "persona_sample_12.csv"

TACTICS = ["authority", "urgency", "trust_building", "fear_induction"]

def _parse_trait_label(value):
    if isinstance(value, dict):
        return value.get("label")
    if isinstance(value, str):
        try:
            return ast.literal_eval(value).get("label")
        except (ValueError, SyntaxError):
            return "unknown"
    return "unknown"

def load_persona_traits():
    df = pd.read_csv(PERSONA_FILE)
    df["agree_label"] = df["agreeableness"].apply(_parse_trait_label)
    df["agree_bucket"] = df["agree_label"].apply(lambda l: "low" if l in ("very low", "low") else "high" )
    df["age_bracket"] = df["age"].apply(lambda a: "18-30" if a<=30 else ("31-50" if a<=50 else "51-70+"))
    return df.set_index("uuid")[["sex", "age_bracket", "agree_bucket"]]

def build_conversation_metrics(conversations, persona_traits):
    rows = []
    for conv in conversations:
        uuid = conv["persona_uuid"]
        if uuid not in persona_traits.index:
            print(f"WARNING: persona {uuid} not found in persona file, skipping")
            continue
        traits = persona_traits.loc[uuid]
        scammer_turns = [t for t in conv["transcript"] if t.get("speaker") == "scammer"]
        total_scammer_turns = len(scammer_turns)

        turn_to_closure = None
        retreat_count = 0
        tactic_counts = {t: 0 for t in TACTICS}

        for idx, t in enumerate(scammer_turns, start=1):
            if t.get("relabel_phase") == "closure_attempt" and turn_to_closure is None:
                turn_to_closure = idx
            if t.get("relabel_retreat"):
                retreat_count += 1
            for tag in t.get("relabel_tactics", []):
                if tag in tactic_counts:
                    tactic_counts[tag] += 1

        row = {
            "persona_uuid": uuid,
            "run_number": conv.get("run_number"),
            "sex": traits["sex"],
            "age_bracket": traits["age_bracket"],
            "agree_bucket": traits["agree_bucket"],
            "total_victim_turns": total_scammer_turns,
            "closure_duration": turn_to_closure if turn_to_closure else total_scammer_turns,
            "closure_observed": 1 if turn_to_closure else 0,
            "retreat_count": retreat_count,
            "retreat_rate": retreat_count/total_scammer_turns if total_scammer_turns else 0,
        }
        row.update({f"{t}_count": c for t, c in tactic_counts.items()})
        rows.append(row)
    return pd.DataFrame(rows)

"""
For every scammer retreat turn what was the immediately preceding
victim turn's suspicion level - compared against baseline distribution 
across all victim turns.
"""
def analyze_retreat_triggers(conversations):
    retreat_preceding_suspicion = []
    all_victim_suspicion = []

    for conv in conversations:
        transcript = conv["transcript"]
        for i, turn in enumerate(transcript):
            if turn.get("speaker") == "victim":
                all_victim_suspicion.append(turn.get("relabel_suspicion"))
            if turn.get("speaker") == "scammer" and turn.get("relabel_retreat"):
                if i > 0 and transcript[i-1].get("speaker") == "victim":
                    retreat_preceding_suspicion.append(transcript[i-1].get("relabel_suspicion"))

    retreat_counts = pd.Series(retreat_preceding_suspicion).value_counts()
    baseline_counts = pd.Series(all_victim_suspicion).value_counts()

    print("\nRetreat Trigger Analysis")
    print(f"Retreats with an identifiable preceding victim turn: {len(retreat_preceding_suspicion)}")
    print("\nSuspicion level immediately before a scammer retreat:")
    print((retreat_counts/retreat_counts.sum()).round(3))
    print("\nBaseline suspicion level across all victim turns:")
    print((baseline_counts/baseline_counts.sum()).round(3))

    # Chi-square test
    categories = sorted(set(retreat_counts.index) | set(baseline_counts.index))
    contingency = pd.DataFrame({
        "retreat_preceding": [retreat_counts.get(c, 0) for c in categories],
        "baseline": [baseline_counts.get(c, 0) for c in categories],
    }, index=categories)
    chi2, p, dof, expected = chi2_contingency(contingency.T)
    print(f"\nChi-square test (retreat-preceding vs baseline distribution): p = {p:.4f}")
    return contingency

def run_survival_analysis(df, duration_col, observed_col, group_col, label):
    print(f"\nTime to {label}, by {group_col}")
    groups = df[group_col].unique()

    kmf = KaplanMeierFitter()

    for group in groups:
        sub = df[df[group_col] == group]
        kmf.fit(sub[duration_col], event_observed=sub[observed_col], label =str(group))
        print(f"    {group}: n={len(sub)}, events={sub[observed_col].sum()}, median turns={kmf.median_survival_time_}")

    if len(groups) == 2:
        g1, g2 = groups
        d1, d2 = df[df[group_col] == g1], df[df[group_col] == g2]
        result = logrank_test (d1[duration_col], d2[duration_col], event_observed_A=d1[observed_col], event_observed_B=d2[observed_col])
        print(f"    Log rank test: p = {result.p_value:.4f}")
    else:
        result = multivariate_logrank_test(df[duration_col], df[group_col], df[observed_col])
        print(f"    Multivariate log rank test: p = {result.p_value:.4f}")

def run_group_comparison(df, value_col, group_col):
    print(f"\n{value_col}, by {group_col}")
    groups = df[group_col].unique()
    for group in groups:
        sub = df[df[group_col] == group]
        print(f"    {group}: n={len(sub)}, mean={sub[value_col].mean():.2f}")

    if len(groups) == 2:
        g1, g2 = groups
        d1 = df[df[group_col] == g1][value_col]
        d2 = df[df[group_col] == g2][value_col]
        stat, p = mannwhitneyu(d1,d2)
        print(f"    Mann-Whitney U: p = {p:.4f}")
    else:
        samples = [df[df[group_col] == group][value_col] for group in groups]
        stat, p = kruskal(*samples)
        print(f"    Kruskal-Wallis: p = {p:.4f}")

def main():
    with open(RELABELED_FILE) as f:
        conversations = json.load(f)

    persona_traits = load_persona_traits()
    df = build_conversation_metrics(conversations, persona_traits)
    df.to_csv("scammer_conversation_metrics.csv", index=False)
    print(f"Built metrics for {len(df)} conversations, saved to 'scammer_conversation_metrics.csv'")

    analyze_retreat_triggers(conversations)

    for group_col in ["agree_bucket", "sex", "age_bracket"]:
        run_survival_analysis(df, "closure_duration", "closure_observed", group_col, "first closure_attempt")
        run_group_comparison(df, "retreat_rate", group_col)
        for tactic in TACTICS:
            run_group_comparison(df, f"{tactic}_count", group_col)
            
if __name__ == "__main__":
    main()