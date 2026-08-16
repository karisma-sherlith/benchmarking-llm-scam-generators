""""
Generates Kaplan-Meier survival curves for suspicion onset,
by agreeableness group. (Proof for same median different shape from
log rank test.) Reuses the 'victim_conversation_metrics.csv' from
analyze_victin.py.
"""

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from lifelines import KaplanMeierFitter

df = pd.read_csv("victim_conversation_metrics.csv")

fig, axes = plt.subplots(1, 2, figsize=(14,5))

for ax, duration_col, observed_col, title in [
    (axes[0], "mild_duration", "mild_observed", "Time to mild-or-higher suspicion, by agreeableness"),
    (axes[1], "high_duration", "high_observed", "Time to high suspicion, by agreeableness"),
]:
    for group, color in [("high", "#4C72B0"), ("low", "#C44E52")]:
        sub = df[df["agree_bucket"] == group]
        kmf = KaplanMeierFitter()
        kmf.fit(sub[duration_col], event_observed=sub[observed_col], label=f"{group} agreeableness")
        kmf.plot_survival_function(ax=ax, color=color)
    ax.set_title(title)
    ax.set_xlabel("Victim turn number")
    ax.set_ylabel("Proportion not yet reached (survival probability)")

plt.tight_layout()
plt.savefig("victim_suspicion_survival_curved.png", dpi=150)
print("Saved 'victim_suspicion_survival_curved.png'")