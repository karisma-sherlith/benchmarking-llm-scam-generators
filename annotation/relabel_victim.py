"""
Implements the victim side re-labelling rubric
2 independent per turn dimensions - 1 for suspicion level and 1 for engagement level
judged with full conversation context up to and including each turn.

Reads conversation_full_batch.json from our final generation
and writes conversations_relabeled_victim.json with new fields added per turn.
"""

import os
import json
import time
from openai import OpenAI
from dotenv import load_dotenv

INPUT_FILE = "conversation_full_batch.json"
OUTPUT_FILE = "conversation_relabeled_victim.json"
MODEL = "gpt-4.1-mini-2025-04-14"

TOTAL_USAGE = {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0}  # TO TRACK API CALL USAGE

load_dotenv()
client = OpenAI(
    api_key = os.getenv("ELM_API_KEY"),
    base_url = "https://api.openai.com/v1",
)

RUBRIC_PROMPT = """
You are annotating one turn of a synthetic pig-butchering scam conversation,
for academic research purposes. You will see the full conversation so far,
ending with the VICTIM turn you need to label.

Label this turn on two INDEPENDENT dimensions:

SUSPICION LEVEL - "none" / "mild" / "high":
- none: normal conversation, no scam-relevant content or wariness.
- mild: a first sign of caution - a polite deflection, changing subject away from money once, a soft boundary.
- high: explicit, clearly-stated wariness - directly naming discomfort (e.g. I am not comfortable discussing this etc.), repeated firm refusals, or questioning the other person's legitimacy.

IMPORTANT: suspicion can go up OR down across the conversation - do not assume
it must stay high once reached. Only increase the level from the previous victim turn if you see ONE of these:
1. Explicit callback/meta-commentary (victim directly names a repeated pattern)
2. Firmness escalation (hedged language -> direct/terse language)
3. New content not present in earlier refusals (e.g. a new statement of distrust)
Near-identical repetition of an earlier refusal, with NONE of the above, should be coded the SAME level as the previous
victim turn, not higher - likely a generation artifact, not real escalation.

ENGAGEMENT LEVEL - "avoidant" / "neutral" / "curious" / "soft_compliance" / "hard_compliance":
- avoidant: actively steers away from the investment/financial topic.
- neutral: acknowledges the topic exists but doesn't engage further either way.
- curious: asks genuine questions about how it works, shows interest, without committing to anything.
- soft_compliance: agrees to a concrete next step short of financial commitment (e.g. "send me the details", agreeing to join a different channel).
- hard_compliance: agrees to an actual financial action (sending money, sharing financial/account details, confirming an investment).

Respond with ONLY valid JSON in exactly this format:
{{"suspicion_level": "none"|"mild"|"high", "engagement_level": "avoidant"|"neutral"|"curious"|"soft_compliance"|"hard_compliance",
"rationale": "<one sentence, max 20 words>"}}

CONVERSATION SO FAR (ending with the turn to label):
{conversation_context}
"""

def _strip_code_fences(text):
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return text

"""
Builds a readable conversation transcript from turn 0 up to an including up to index. 
Uses raw as fallback for parse failure turns
"""
def build_context_string(transcript, up_to_index):
    lines = []
    for turn in transcript[:up_to_index + 1]:
        speaker = turn.get("speaker", "unknown")
        msg = turn.get("message") or turn.get("raw") or "[no content]"
        lines.append(f"{speaker.upper()}: {msg}")
    return "\n".join(lines)

def relabel_turn(conversation_context, max_retries=2):
    prompt = RUBRIC_PROMPT.format(conversation_context=conversation_context)

    last_raw = None
    for attempt in range(max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model= MODEL,
                messages= [{"role": "user", "content": prompt}],
                temperature=0,
                response_format= {"type": "json_object"},
                )
        except Exception as e:
            print(f"API calls failed (attempt {attempt+1}): {e}")
            time.sleep(1)
            continue

        # TO TRACK API CALL USAGE 
        TOTAL_USAGE["prompt_tokens"] += resp.usage.prompt_tokens
        TOTAL_USAGE["completion_tokens"] += resp.usage.completion_tokens
        TOTAL_USAGE["calls"] += 1
        
        raw = resp.choices[0].message.content or resp.choices[0].message.refusal

        last_raw = raw
        if raw is None:
            print(f"Got None content, finish_reason={resp.choices[0].finish_reason}")
            time.sleep(0.5)
            continue

        cleaned = _strip_code_fences(raw)
        try:
            parsed = json.loads(cleaned)
            if "suspicion_level" in parsed and "engagement_level" in parsed:
                return parsed
            else:
                print(f"Missing expected keys (attempt {attempt+1}): {parsed}")
        except json.JSONDecodeError:
            print(f"JSON parse failed (attempt {attempt+1}): {cleaned[:200]}")

        time.sleep(0.5)

    return {"suspicion_level": "LABEL_FAILURE", "engagement_level": "LABEL_FAILURE", "rationale": None, "raw": last_raw}

def main():
    with open(INPUT_FILE) as f:
        conversations = json.load(f)

    conversations = conversations[:2] # TEMPORARY TEST LIMIT

    for conv in conversations:
        transcript = conv["transcript"]
        print(f"Relabelling persona {conv['persona_uuid'][:8]}, run {conv.get('run_number')}...")

        for i, turn in enumerate(transcript):
            if turn.get("speaker") != "victim":
                continue
            context = build_context_string(transcript, i)
            labels = relabel_turn(context)
            turn["relabel_suspicion"]  = labels["suspicion_level"]
            turn["relabel_engagement"] = labels["engagement_level"]
            turn["relabel_rationale"] = labels.get("rationale")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(conversations, f, indent=2)
    print("Saved conversation_relabeled_victim.json")
    
    # PRINTING ACTUAL API COST
    input_cost = TOTAL_USAGE["prompt_tokens"] / 1_000_000 * 0.40
    output_cost = TOTAL_USAGE["completion_tokens"] / 1_000_000 * 1.6
    print(f"Total API Calls: {TOTAL_USAGE['calls']}")
    print(f"Total Tokens: {TOTAL_USAGE['prompt_tokens']} in, {TOTAL_USAGE['completion_tokens']} out")
    print(f"Estimated Cost: ${input_cost + output_cost:.4f}")
    
if __name__ == "__main__":
    main()