"""
Implements the scammer side re-labelling rubric
phase, pressure_direction, and tactic tags per turn,
judged with full conversation context up to and including each turn.
Retreat and retreat trigger are NOT judged here - computed afterward from 
phase/pressure direction, once per conversation, as mentioned in the rubric.

Reads conversation_relabeled_victim.json from the victim relabel script,
so both sets of labels end up in the same file.
"""

import os
import json
import time
from openai import OpenAI
from dotenv import load_dotenv

INPUT_FILE = "conversation_relabeled_victim.json"
OUTPUT_FILE = "conversation_relabeled_full.json"
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
ending with the SCAMMER turn you need to label.

Label this turn on THREE dimensions:

PHASE - "hook" / "vetting" / "closure_attempt" / "neutral_conversation":
- hook: actively building rapport/trust, presentic as a genuine interest.
- vetting: learning more about the targey and/or beginning to introduce the investment opportunity.
- closure_attempt: actively pushing for a concrete commitment (money, financial details, joining a platform).
- neutral_conversation: replying to something the victim raised, or general conversation, with no rapport-building or investment intetn either way.

PRESSURE DIRECTION - "escalating" / "steady" / "de-escalating":
Compare this turn's intensity to the scammer's PREVIOUS turn, not the conversation as a whole.
- escalating: pushing harder than the previous turn - more direct, more urgent, more insistent.
- steady: consistent intensity with the previous turn.
- de-escalating: backing off - softer tone, dropping the topic, returning to casual conversation, even if the phase label hasn't categorically changed.
(For the very first scammer turn in a conversation, use "steady" as there is no previous turn to compare against.)

TACTIC TAGS - list, choose ALL that apply (can be empty list if none):
- "authority": claims of special access, credentials, or insider knowledge.
- "urgency": time pressure or scarcity framing.
- "trust_building": vouches, compliments, appeals to reputation or track record.
- "fear_induction": implying loss, missed opportunity, or risk to the relationship if the victim hesitates.

Respond with ONLY valid JSON in exactly this format:
{{"phase": "hook"|"vetting"|"closure_attempt"|"neutral_conversation", "pressure_direction": "escalating"|"steady"|"de-escalating",
"tactic_tags": ["authority", "urgency", "trust_building", "fear_induction"] (empty list if none), "rationale": "<one sentence, max 20 words>"}}

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
            if all(key in parsed for key in ("phase", "pressure_direction", "tactic_tags")):
                return parsed
            else:
                print(f"Missing expected keys (attempt {attempt+1}): {parsed}")
        except json.JSONDecodeError:
            print(f"JSON parse failed (attempt {attempt+1}): {cleaned[:200]}")

        time.sleep(0.5)
        
    return {"phase": "LABEL_FAILURE", "pressure_direction": "LABEL_FAILURE", "tactic_tags": [],"rationale": None, "raw": last_raw}

def compute_retreats(transcript):
    phase_order = {"hook": 0, "vetting": 1, "closure_attempt": 2, "neutral_conversation": None}

    scammer_turns = [t for t in transcript if t.get("speaker") == "scammer"]
    prev_phase_rank = None
    for turn in scammer_turns:
        phase = turn.get("relabel_phase")
        pressure = turn.get("relabel_pressure")
        rank = phase_order.get(phase)

        phase_retreat = (prev_phase_rank is not None and rank is not None and rank<prev_phase_rank)
        pressure_retreat = pressure == "de-escalating"

        turn["relabel_retreat"] = bool(phase_retreat or pressure_retreat)

        if rank is not None:
            prev_phase_rank = rank

def main():
    with open(INPUT_FILE) as f:
        conversations = json.load(f)

    conversations = conversations[:2] # TEMPORARY TEST LIMIT

    for conv in conversations:
        transcript = conv["transcript"]
        print(f"Relabelling persona {conv['persona_uuid'][:8]}, run {conv.get('run_number')}...")

        for i, turn in enumerate(transcript):
            if turn.get("speaker") != "scammer":
                continue
            context = build_context_string(transcript, i)
            labels = relabel_turn(context)
            turn["relabel_phase"]  = labels["phase"]
            turn["relabel_pressure"] = labels["pressure_direction"]
            turn["relabel_tactics"] = labels.get("tactic_tags", [])
            turn["relabel_rationale"] = labels.get("rationale")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(conversations, f, indent=2)
    print("Saved conversation_relabeled_full.json")
    
    # PRINTING ACTUAL API COST
    input_cost = TOTAL_USAGE["prompt_tokens"] / 1_000_000 * 0.40
    output_cost = TOTAL_USAGE["completion_tokens"] / 1_000_000 * 1.6
    print(f"Total API Calls: {TOTAL_USAGE['calls']}")
    print(f"Total Tokens: {TOTAL_USAGE['prompt_tokens']} in, {TOTAL_USAGE['completion_tokens']} out")
    print(f"Estimated Cost: ${input_cost + output_cost:.4f}")
    
if __name__ == "__main__":
    main()