(venv) C:..../benchmarking-llm-scam-generators/annotation/persona\_distinctiveness\_check.py

Leave one out accuracy: 0.25 (3/12)

Chance baseline (always guess majority class): 0.50



Per-persona predictions:

&#x20;   0b0041b8...  actual=high   predicted=low    \[WRONG]

&#x20;   31ad5165...  actual=high   predicted=low    \[WRONG]

&#x20;   266f8c14...  actual=low    predicted=low    \[correct]

&#x20;   5ee84b2e...  actual=high   predicted=low    \[WRONG]

&#x20;   50bc1d81...  actual=low    predicted=high   \[WRONG]

&#x20;   18bcda3d...  actual=low    predicted=high   \[WRONG]

&#x20;   1d7e079d...  actual=high   predicted=low    \[WRONG]

&#x20;   0b0f8f2b...  actual=low    predicted=high   \[WRONG]

&#x20;   4448c8e7...  actual=high   predicted=high   \[correct]

&#x20;   534031b6...  actual=high   predicted=high   \[correct]

&#x20;   50ffb81e...  actual=low    predicted=high   \[WRONG]

&#x20;   05d360b1...  actual=low    predicted=high   \[WRONG]



Feature importances (descriptive only, fit on all 12):

&#x20;   age: 0.400

&#x20;   extraversion\_label\_high: 0.333

&#x20;   conscientiousness\_label\_average: 0.267







#### **MANUAL BLIND TEST**

|ID|PREDICTION|ACTUAL|CORRECT|REASON|
|-|-|-|-|-|
|P01|LOW|LOW|YES||
|P02|LOW|LOW|YES||
|P03|HIGH|HIGH|YES||
|P04|LOW|LOW|YES||
|P05|LOW|LOW|YES||
|P06|HIGH|LOW|NO|"curious nature", "ambitious individual", "outgoing and energetic individual"<br />|
|P07|HIGH|HIGH|YES||
|P08|LOW|LOW|YES||
|P09|HIGH|HIGH|YES||
|P10|LOW|HIGH|NO|"financially savvy, prioritizing saving and budgeting", "practicality"<br />|
|P11|HIGH|HIGH|YES||
|P12|HIGH|HIGH|YES||



CORRECT = 10/12

INCORRECT = 2/12



the probability of getting 10-or-more correct by pure random guessing is about 1.9% (one-tailed binomial; \~3.9% two-tailed) — both comfortably under the conventional 5% threshold. So this is legitimately reportable as:

***"blind manual review achieved 83% accuracy (10/12) distinguishing agreeableness level from persona text alone, significantly above the 50% chance baseline (p ≈ 0.02)."***

The first (guessed high, actual low) was misled by "curious nature," "ambitious," "outgoing and energetic" — that's openness/extraversion language, not agreeableness. The second (guessed low, actual high) was misled by "financially savvy, prioritizing saving and budgeting," "practicality" — finance-focused, self-interest-adjacent language that reads as low-agreeableness on the surface but wasn't.

