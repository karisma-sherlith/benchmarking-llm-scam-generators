""""
Builds turn by turn conversation loop betweeen scammer and victim.
Structured Turns: each turn, both models return
{"message":.... , "status":....}
So that the loop knows when to stop.
Else if a max turn is set, conversation could still run if victim already disengaged.
Wasting API calls.

VICTIM STATUS:
    - continue: normal back and forth, keep going
    - suspicious: victim starts feeling suspicious but not disengaged yet
    - blocked: disengages conversation
    - complied: agreed/fell for the scam

SCAMMER STATUS:
    - tracks which phase it believes it is in
    - scammer's own self reported phase
    - need to compare against victim's actual status in analysis
    - hook / vetting / closure attempt

STOPPING CONDITIONS:
    - checked after each victim turn
    - if blocked or complied, stop conversation
    - turn count hits MAX_TURNS to stop as a safety net if conversation is not leading anywhere to avoid unnecessary calls.

NOTES:
    - Status fields are self reported by each model.
    - Needs to spot check sample as it could still misreport.
    - Max turns is just random - safety net.
    - Needs to be changed depending on test run and checking conversation lengths.
"""

import os
import json
import time
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from prompts import build_victim_system_prompt, build_scammer_starting_info, build_scammer_system_prompt

MODEL = "gpt-4.1-mini-2025-04-14"
MAX_TURNS = 20

load_dotenv()
client = OpenAI(
    api_key = os.getenv("ELM_API_KEY"),
    base_url = "https://api.openai.com/v1",
)

"""Models wrap JSON IN ```json...``` sometimes even when asked not to"""
def _strip_code_fences(text):
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return text

"""
Calls the model and gets {message:..., status:...}
Retries on parse failure before giving up
Role label is just scammer and victim
"""
def call_llm(system_prompt, conversation_history, role_label, max_retries=2):
    messages = [{"role":"system","content":system_prompt}]
    for turn in conversation_history:
        messages.append(turn)

    last_raw = None
    for attempt in range(max_retries+1):
        try:
            resp = client.chat.completions.create(
                model = MODEL,
                messages = messages,
                temperature = 0.7,
                response_format = {"type":"json_object"},
            )
        except Exception as e:
            print(f"[{role_label}] API Call failed (attempt {attempt+1}): {e}")
            time.sleep(1)
            continue

        raw = resp.choices[0].message.content or resp.choices[0].message.refusal
        last_raw = raw
        if raw is None:
            finish_reason = resp.choices[0].finish_reason
            print(f"[{role_label}] Got None content. finish_reason={finish_reason}")
            print(f"[{role_label}] Full response object: {resp}")
            time.sleep(0.5)
            continue
        cleaned = _strip_code_fences(raw)

        try:
            parsed = json.loads(cleaned)
            if "message" in parsed and "status" in parsed:
                return parsed
            else:
                print(f"[{role_label}] JSON parsed but missing expected keys (attempt {attempt+1}): {parsed}")
        except json.JSONDecodeError:
            print(f"[{role_label}] JSON parse failed (attempt {attempt+1}): {cleaned[:200]}")
        time.sleep(0.5)

        # If all retires failed return a marked failure and not crash whole conversation

    return {"message": None, "status": "PARSE_FAILURE", "raw": last_raw}

"""
Runs 1 full conversation between scammer and victim for a given persona
Returns a dict with full conversation and how it ended
"""
def run_conversation(persona_row, max_turns=MAX_TURNS):
    victim_system = build_victim_system_prompt(persona_row)
    starting_info = build_scammer_starting_info(persona_row)
    scammer_system = build_scammer_system_prompt(starting_info)

    json_instruction = '\n\nRespond with ONLY valid JSON in exactly this format: {"message": "<your chat message>", "status": "<see your role instructions for valid status values>"}'

    victim_status_criteria = '''
    Valid status values, and exactly when to use each one:
    - "continue": your default status - use this for most turns, while the conversation feels like normal, comfortable getting-to-know-you conversation.
    - "suspicious": use this once something has started to feel off to you - e.g. they're asking for money or financial details, pushing you to make a decision quickly, mentioning an investment/opportunity,
    or being evasive about meeting in person or verifying who they are. You can stay in "suspicious" for multiple turns while you're still engaging but wary.
    - "blocked": use this the turn you decide to stop responding/end contact with this person, because your suspicion has crossed a threshold your personality would find
    unacceptable (e.g. they've directly asked for money, or the inconsistenciesare too much). This ends the conversation.
    "complied": use this the turn you actually agree to a concrete action they've asked for - e.g. agreeing to send money, share financial/account details, or invest in something they've proposed. 
    This ends the conversation.
    Base WHEN you move between these on the personality profile above, not on a fixed script - a low-agreeableness or high-neuroticism person might move to "suspicious" faster than a high-agreeableness person, for example.
    '''

    victim_system_full = victim_system + json_instruction + victim_status_criteria
    scammer_system_full = scammer_system + json_instruction + \
    '\nValid status values: "hook", "vetting", "closure_attempt"'

    transcript = []
    scammer_history = []
    victim_history = []

    ended_reason = "max_turns_reached"

    for turn_num in range(1, max_turns+1):
        scammer_result = call_llm(scammer_system_full, scammer_history, "scammer")
        if scammer_result["status"] == "PARSE_FAILURE":
            ended_reason = "scammer_parse_failure"
            transcript.append({"turn": turn_num, "speaker": "scammer", **scammer_result})
            break
        
        transcript.append({"turn": turn_num, "speaker": "scammer", **scammer_result})
        scammer_history.append({"role": "assistant", "content": scammer_result["message"]})
        victim_history.append({"role": "user", "content": scammer_result["message"]})

        # Victim Responds
        victim_result = call_llm(victim_system_full, victim_history, "victim")
        if victim_result["status"] == "PARSE_FAILURE":
            ended_reason = "victim_parse_failure"
            transcript.append({"turn": turn_num, "speaker": "victim", **victim_result})
            break

        transcript.append({"turn": turn_num, "speaker": "victim", **victim_result})
        victim_history.append({"role": "assistant", "content": victim_result["message"]})
        scammer_history.append({"role": "user", "content": victim_result["message"]})

        if victim_result["status"] in ("blocked", "complied"):
            ended_reason = victim_result["status"]
            break

    return {
        "persona_uuid": persona_row["uuid"],
        "transcript": transcript,
        "ended_reason": ended_reason,
        "total_turns": turn_num,
    }

"""
Loads 12 persona sample and runs 1 conversation for test
Later 3-5 runs for each persona
"""
def main():
    personas = pd.read_csv("persona_sample_12.csv")
    results = []
    for _, persona_row in personas.iterrows():
        print(f"Running conversation for persona {persona_row['uuid']}...")
        result = run_conversation(persona_row)
        results.append(result)
        print(f"    -> ended: {result['ended_reason']} after {result['total_turns']} turns")

    with open ("conversation_test_batch.json","w") as f:
        json.dump(results, f, indent=2)
    print("Saved conversations_test_batch.json")


if __name__ == "__main__":
    main()