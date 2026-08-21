# **PHASE 3 FINDINGS**

##### 

##### VICTIM RELABEL OUTPUT

Saved conversation\_relabeled\_victim.json

Total API Calls: 1674

Total Tokens: 3954277 in, 67656 out

Estimated Cost: $1.6900



"relabel\_suspicion" : 1674 total, 791 none, 783 mild, 100 high

"relabel\_engagement" : 1674 total, 130 avoidant, 761 neutral, 649 curious, 134 soft\_compliance, 0 hard\_compliance





##### BLIND REVIEW - VICTIM

Sampled suspicion:

&#x20; none : 10 / 8

&#x20; mild : 13 / 8

&#x20; high :  9 / 8



Sampled engagement:

&#x20; avoidant        :  8 / 8

&#x20; neutral         :  8 / 8

&#x20; curious         :  8 / 8

&#x20; soft\_compliance :  8 / 8



###### ***Cohen's kappa indicated substantial agreement for both dimensions, with stronger agreement for suspicion level (κ = .814) than for engagement level (κ = .708).***





##### SCAMMER RELABEL OUTPUT

Saved conversation\_relabeled\_full.json

Total API Calls: 1675

Total Tokens: 3827507 in, 81289 out

Estimated Cost: $1.6611



"relabel\_phase": total 1675, 244 hook, 535 vetting, 415 closure attempt, 481 neutral

"relabel\_pressure": total 1675, 713 steady, 464 escalating, 498 de escalating

"relabel\_tactics": total 1675, 300 authority, 1076 trust building, 250 urgency, 89 fear induction

"relabel\_retreat": total 1675, 1037 false, 638 true



***Worth keeping in mind as you design the retreat-trigger cross-reference against victim suspicion later — with this much data, that analysis should have real statistical footing, not just a handful of examples.***



##### BLIND REVIEW - SCAMMER

Sampled Phase: hook = 8, vetting = 8, closure\_attempt = 8, neutral\_conversation = 8



Sampled Pressure: steady = 17, escalating = 7, de-escalating = 8



Sampled Tactic: authority y=9 n=23, urgency y=4 n=28, trust\_building y=21 n=11, fear\_induction y=4 n=28



###### ***Cohen’s kappa was calculated separately for the six annotation dimensions. The results indicated substantial to perfect agreement across most dimensions: Phase (κ = .708), Pressure (κ = .755), Authority (κ = .847), Urgency (κ = .767), and Fear Induction (κ = 1.000). Trust Building at κ=0.603 technically falls just at the edge of "moderate" (0.41–0.60), not cleanly "substantial" (0.61–0.80) by the standard Landis \& Koch bands.Fear Induction demonstrated perfect agreement, while Authority showed the highest agreement among the remaining dimensions.***  ***It likely reflects that "is this trust-building" is a genuinely fuzzier judgment call than something more binary like fear\_induction (which is rare and usually unambiguous when present). Overall, the results indicate a high level of consistency between the blind-review guesses and the actual annotations.***



##### VICTIM ANALYSIS (FINAL)

Built metrics for 60 conversations, saved to 'victim\_conversation\_metrics.csv'



Time to mild suspicion onset by agree\_bucket

&#x20;   high: n=30, events=30, median turns to event=4.0

&#x20;   low: n=30, events=30, median turns to event=4.0

&#x20;   Log rank test: p = 0.0138



Time to high suspicion onset by agree\_bucket

&#x20;   high: n=30, events=3, median turns to event=inf

&#x20;   low: n=30, events=21, median turns to event=13.0

&#x20;   Log rank test: p = 0.0000



Max engagement reached by agree\_bucket

&#x20;   high: n=30, mean max engagement=2.70

&#x20;   low: n=30, mean max engagement=2.43

&#x20;   Mann-Whitney U: p = 0.0396



Time to mild suspicion onset by sex

&#x20;   Male: n=30, events=30, median turns to event=4.0

&#x20;   Female: n=30, events=30, median turns to event=4.0

&#x20;   Log rank test: p = 0.8989



Time to high suspicion onset by sex

&#x20;   Male: n=30, events=9, median turns to event=inf

&#x20;   Female: n=30, events=15, median turns to event=25.0

&#x20;   Log rank test: p = 0.1665



Max engagement reached by sex

&#x20;   Male: n=30, mean max engagement=2.57

&#x20;   Female: n=30, mean max engagement=2.57

&#x20;   Mann-Whitney U: p = 1.0000



Time to mild suspicion onset by age\_bracket

&#x20;   18-30: n=20, events=20, median turns to event=4.0

&#x20;   31-50: n=20, events=20, median turns to event=4.0

&#x20;   51-70+: n=20, events=20, median turns to event=4.0

&#x20;   Multivariate log rank test: p = 0.4965



Time to high suspicion onset by age\_bracket

&#x20;   18-30: n=20, events=10, median turns to event=25.0

&#x20;   31-50: n=20, events=7, median turns to event=inf

&#x20;   51-70+: n=20, events=7, median turns to event=inf

&#x20;   Multivariate log rank test: p = 0.7204



Max engagement reached by age\_bracket

&#x20;   18-30: n=20, mean max engagement=2.75

&#x20;   31-50: n=20, mean max engagement=2.60

&#x20;   51-70+: n=20, mean max engagement=2.35

&#x20;   Kruskal-Wallis: p = 0.0380





##### SCAMMER ANALYSIS (FINAL)

Built metrics for 60 conversations, saved to 'scammer\_conversation\_metrics.csv'



Retreat Trigger Analysis

Retreats with an identifiable preceding victim turn: 638



Suspicion level immediately before a scammer retreat:

mild    0.516

none    0.368

high    0.116

Name: count, dtype: float64



Baseline suspicion level across all victim turns:

none    0.473

mild    0.468

high    0.060

Name: count, dtype: float64



Chi-square test (retreat-preceding vs baseline distribution): p = 0.0000



Time to first closure\_attempt, by agree\_bucket

&#x20;   high: n=30, events=29, median turns=7.0

&#x20;   low: n=30, events=29, median turns=8.0

&#x20;   Log rank test: p = 0.4541



retreat\_rate, by agree\_bucket

&#x20;   high: n=30, mean=0.34

&#x20;   low: n=30, mean=0.40

&#x20;   Mann-Whitney U: p = 0.0286



authority\_count, by agree\_bucket

&#x20;   high: n=30, mean=4.63

&#x20;   low: n=30, mean=5.37

&#x20;   Mann-Whitney U: p = 0.2872



urgency\_count, by agree\_bucket

&#x20;   high: n=30, mean=5.53

&#x20;   low: n=30, mean=2.80

&#x20;   Mann-Whitney U: p = 0.0570



trust\_building\_count, by agree\_bucket

&#x20;   high: n=30, mean=18.50

&#x20;   low: n=30, mean=17.37

&#x20;   Mann-Whitney U: p = 0.2261



fear\_induction\_count, by agree\_bucket

&#x20;   high: n=30, mean=2.17

&#x20;   low: n=30, mean=0.80

&#x20;   Mann-Whitney U: p = 0.0147



Time to first closure\_attempt, by sex

&#x20;   Male: n=30, events=29, median turns=7.0

&#x20;   Female: n=30, events=29, median turns=8.0

&#x20;   Log rank test: p = 0.3400



retreat\_rate, by sex

&#x20;   Male: n=30, mean=0.34

&#x20;   Female: n=30, mean=0.41

&#x20;   Mann-Whitney U: p = 0.0227



authority\_count, by sex

&#x20;   Male: n=30, mean=5.13

&#x20;   Female: n=30, mean=4.87

&#x20;   Mann-Whitney U: p = 0.9761



urgency\_count, by sex

&#x20;   Male: n=30, mean=4.67

&#x20;   Female: n=30, mean=3.67

&#x20;   Mann-Whitney U: p = 0.5258



trust\_building\_count, by sex

&#x20;   Male: n=30, mean=17.70

&#x20;   Female: n=30, mean=18.17

&#x20;   Mann-Whitney U: p = 0.9349



fear\_induction\_count, by sex

&#x20;   Male: n=30, mean=1.60

&#x20;   Female: n=30, mean=1.37

&#x20;   Mann-Whitney U: p = 0.6400



Time to first closure\_attempt, by age\_bracket

&#x20;   18-30: n=20, events=18, median turns=7.0

&#x20;   31-50: n=20, events=20, median turns=7.0

&#x20;   51-70+: n=20, events=20, median turns=10.0

&#x20;   Multivariate log rank test: p = 0.5149



retreat\_rate, by age\_bracket

&#x20;   18-30: n=20, mean=0.35

&#x20;   31-50: n=20, mean=0.38

&#x20;   51-70+: n=20, mean=0.39

&#x20;   Kruskal-Wallis: p = 0.6957



authority\_count, by age\_bracket

&#x20;   18-30: n=20, mean=4.95

&#x20;   31-50: n=20, mean=4.70

&#x20;   51-70+: n=20, mean=5.35

&#x20;   Kruskal-Wallis: p = 0.8623



urgency\_count, by age\_bracket

&#x20;   18-30: n=20, mean=6.50

&#x20;   31-50: n=20, mean=4.15

&#x20;   51-70+: n=20, mean=1.85

&#x20;   Kruskal-Wallis: p = 0.0031



trust\_building\_count, by age\_bracket

&#x20;   18-30: n=20, mean=17.20

&#x20;   31-50: n=20, mean=18.70

&#x20;   51-70+: n=20, mean=17.90

&#x20;   Kruskal-Wallis: p = 0.3532



fear\_induction\_count, by age\_bracket

&#x20;   18-30: n=20, mean=1.85

&#x20;   31-50: n=20, mean=1.50

&#x20;   51-70+: n=20, mean=1.10

&#x20;   Kruskal-Wallis: p = 0.7476



##### OUTCOME ANALYSIS (FINAL)

How conversations ended (n=60)

max\_turns\_reached        48

victim\_parse\_failure      7

blocked                   4

scammer\_parse\_failure     1

Name: count, dtype: int64



Mean total turns: 27.9, median: 30



Merged metrics for 60 conversations, saved to 'outcome\_merged\_metrics.csv'



Does retreat rate correlate with max engagement reached?

&#x20;   Spearman rho = -0.518, p = 0.0000



Does tactic usage volume correlate with max engagement reached?

&#x20;   authority: rho = -0.122, p = 0.3528

&#x20;   urgency: rho = 0.527, p = 0.0000

&#x20;   trust\_building: rho = 0.233, p = 0.0730

&#x20;   fear\_induction: rho = 0.365, p = 0.0042

