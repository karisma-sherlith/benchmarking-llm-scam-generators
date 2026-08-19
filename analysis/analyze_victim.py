"""
Victim side final analysis, built on the validated (kappa checked)
turn labels from relabel_victim.py.

Three Analyses:
1.  Time to suspicion onset (mild and high) by persona trait
    Kaplan-Meier + log rank test, since some conversations never reach a given suspicion level (censored data)
    excluding those cases or naively comparing turn numbers would bias the result.
2.  Max engagement level reached by persona trait
    Mann-Whitney U (2 group: agreeableness (high/low), sex(m/f))
    Kruskal-Wallis (3 group: age bracket (18-30, 31-50, 51+))
    No censoring issue here since max reached is always known.
3.  Descriptive
    Average suspicion level by turn number, by agreeableness group - a supporting plot.

Caveats:
With only 100/1675 "high" suspicion turn and 0 hard_compliance turns total,
some of these comparisons may come back statistically inconclusive. 
That's a property of the data, not a bug in the method.
"""

import json
import pandas as pd
import numpy as np
from scipy.stats import mannwhitneyu, kruskal
from lifelines import KaplanMeierFitter
from lifelines.statistics import logrank_test, multivariate_logrank_test
import ast

RELABELED_FILE = "conversation_relabeled_full.json"
PERSONA_FILE = "persona_sample_12.csv"

ENGAGEMENT_ORDER = {"avoidant": 0, "neutral": 1, "curious": 2, "soft_compliance": 3, "hard_compliance": 4}

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
        victim_turns = [t for t in conv["transcript"] if t.get("speaker") == "victim"]
        total_turns = len(victim_turns)
        turn_to_mild = None
        turn_to_high = None
        max_engagement = -1

        for idx, t in enumerate(victim_turns, start=1):
            suspicion = t.get("relabel_suspicion")
            engagement = t.get("relabel_engagement")

            if suspicion in ("mild", "high") and turn_to_mild is None:
                turn_to_mild = idx
            if suspicion == "high" and turn_to_high is None:
                turn_to_high = idx
            if engagement in ENGAGEMENT_ORDER:
                max_engagement = max(max_engagement, ENGAGEMENT_ORDER[engagement])

        rows.append({
            "persona_uuid": uuid,
            "run_number": conv.get("run_number"),
            "sex": traits["sex"],
            "age_bracket": traits["age_bracket"],
            "agree_bucket": traits["agree_bucket"],
            "total_victim_turns": total_turns,
            # For survival analysis: duration is the turn reached or total turns, observed is whether event happenned or not
            "mild_duration": turn_to_mild if turn_to_mild else total_turns,
            "mild_observed": 1 if turn_to_mild else 0,
            "high_duration": turn_to_high if turn_to_high else total_turns,
            "high_observed": 1 if turn_to_high else 0,
            "max_engagement": max_engagement,
        })
    return pd.DataFrame(rows)

def run_survival_analysis(df, duration_col, observed_col, group_col, label):
    print(f"\nTime to {label} onset by {group_col}")
    groups = df[group_col].unique()

    kmf = KaplanMeierFitter()
    medians = {}

    for group in groups:
        sub = df[df[group_col] == group]
        kmf.fit(sub[duration_col], event_observed=sub[observed_col], label =str(group))
        medians[group] = kmf.median_survival_time_
        print(f"    {group}: n={len(sub)}, events={sub[observed_col].sum()}, median turns to event={kmf.median_survival_time_}")

    if len(groups) == 2:
        g1, g2 = groups
        d1, d2 = df[df[group_col] == g1], df[df[group_col] == g2]
        result = logrank_test (d1[duration_col], d2[duration_col], event_observed_A=d1[observed_col], event_observed_B=d2[observed_col])
        print(f"    Log rank test: p = {result.p_value:.4f}")
    else:
        result = multivariate_logrank_test(df[duration_col], df[group_col], df[observed_col])
        print(f"    Multivariate log rank test: p = {result.p_value:.4f}")

def run_engagement_comparison(df, group_col):
    print(f"\nMax engagement reached by {group_col}")
    groups = df[group_col].unique()
    for group in groups:
        sub = df[df[group_col] == group]
        print(f"    {group}: n={len(sub)}, mean max engagement={sub['max_engagement'].mean():.2f}")

    if len(groups) == 2:
        g1, g2 = groups
        d1 = df[df[group_col] == g1]["max_engagement"]
        d2 = df[df[group_col] == g2]["max_engagement"]
        stat, p = mannwhitneyu(d1,d2)
        print(f"    Mann-Whitney U: p = {p:.4f}")
    else:
        samples = [df[df[group_col] == group]["max_engagement"] for group in groups]
        stat, p = kruskal(*samples)
        print(f"    Kruskal-Wallis: p = {p:.4f}")

def main():
    with open(RELABELED_FILE) as f:
        conversations = json.load(f)

    persona_traits = load_persona_traits()
    df = build_conversation_metrics(conversations, persona_traits)
    df.to_csv("victim_conversation_metrics.csv", index=False)
    print(f"Built metrics for {len(df)} conversations, saved to 'victim_conversation_metrics.csv'")

    for group_col in ["agree_bucket", "sex", "age_bracket"]:
        run_survival_analysis(df, "mild_duration", "mild_observed", group_col, "mild suspicion")
        run_survival_analysis(df, "high_duration", "high_observed", group_col, "high suspicion")
        run_engagement_comparison(df, group_col)

if __name__ == "__main__":
    main()