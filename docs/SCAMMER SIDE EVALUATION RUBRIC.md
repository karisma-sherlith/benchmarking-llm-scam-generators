# **SCAMMER SIDE EVALUATION**

## **TURN LEVEL RE-LABELLING RUBRIC**



##### **RATIONALE**

The original phase field (hook/vetting/closure\_attempt) assumes the scammer is always actively advancing toward the scam. My manual skim found turns that don't fit this - the scammer simply answering a question or continuing ordinary conversation with no rapport building or investment either way. Forcing these into "hook" would blur two different things deliberate trust-rebuilding after a retreat (which is meaningful to our research question) vs. incidental conversation with no directional intent. I am adding a 4th phase category to separate these.



I am also adding a 2nf, independent dimension for pressure intensity, since phase categories are coarse - softening can happen within a single phase, not just at the boundary between phases (e.g. 2 consecutive turns both labeled "vetting" where 1 clearly backs off in tone.)



##### **DIMENSION 1: PHASE**

Relabelled with full conversation history up to and including that turn available to the judge, same as the victim-side rubric.

* **hook:** actively building rapport/trust, presenting as a genuine interest.
* **vetting:** learning more about the target and/or beginning to introduce the investment opportunity.
* **closure\_attempt:** actively pushing for a concrete commitment (money, financial details, join a platform, click links etc)
* **neutral\_conversation:** replying to something the victim asked, or general conversation, with no rapport building or investment advancing intent either way.



##### **DIMENSION 2: PRESSURE DIRECTION**

Captures within phase intensity change, independent of the phase label itself.

* **escalating:** pushing harder than the previous turn - more direct, more urgent, more insistent.
* **steady:** consistent with the previous turn's intensity.
* **de-escalating:** backing off - softer tone, dropping the topic, returning to casual conversation, even if the phase label hasn't categorically changed.



##### **DIMENSION 3: TACTIC TAGS**

Multi label, reusing the Phase 1 taxonomy exactly, for consistency.

* **authority:** claims of special access, credentials, or insider knowledge.
* **urgency:** time pressure or scarcity framing.
* **trust\_building:** vouches, compliments, appeals to reputation or track record.
* **fear\_induction:** implying loss, missed opportunity, or risk to the relationship if the victim hesitates.



##### **RETREAT**

Not directly asked by LLM (judge). Computed afterward from the 2 dimensions: a turn counts as retreat if either the phase moves backward (e.g. closure\_attempt -> vetting) or the pressure direction reads de-escalating - capturing both between phase and within phase softening.



##### **RETREAT TRIGGER**

Also computed afterward, not asked from the LLM Judge. Each detected retreated is cross-referenced against the victim's suspicion level from the victim side evaluation. If retreats reliably follow a jump to "high" suspicion, that is derived from the data rather than asserted by the judge.



##### **NOT YET COVERED**

* How phase/pressure/tactic codes aggregate into a conversation level summary.
* Exact judge prompt wording.



##### **VALIDATION PLAN**

A subset of judge-coded turns will be manually re-coded independently, with agreement reported using Cohen's Kappa.



