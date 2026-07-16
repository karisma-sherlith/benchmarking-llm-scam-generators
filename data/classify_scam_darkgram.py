"""
Two-stage scam classification pipeline for DarkGram threads, updated to:
  1. Use a 4-way label instead of binary, including "potential_scam" for
     threads that don't confirm an actual scam but show recognized
     manipulation tactics that could plausibly lead to one.
  2. Tag threads with specific manipulation tactics (authority, urgency,
     trust_building, fear_induction) so we can inspect why something
     was flagged, not just the label.
  3. Merge the original post and its replies into a single ordered,
     reply-numbered block (instead of two separate fields), while
     explicitly telling the model NOT to assume it's a single continuous
     dialogue.
  4. Produce TWO outputs: the full annotated CSV, and a filtered CSV of
     scam + potential_scam threads only (for sharing examples/for Phase 2).

LABEL DEFINITIONS BELOW ARE A PROPOSAL, not confirmed with your
   supervisor. Especially "potential_scam" - the line between "shady
   marketplace banter" and "manipulation tactic that could lead to a scam"
   is a judgment call. Read a sample of potential_scam-labeled threads
   yourself before trusting the category.

TACTIC TAGS (authority/urgency/trust_building/fear_induction) are
   proxy for PreScam's turn-level psychological action labels.
   This is NOT a reproduction of their taxonomy. 

NOT NECESSARILY A SINGLE TWO-PARTY DIALOGUE. "Combined Replies" in
   this dataset often looks like multiple different commenters replying
   to a public channel post, not one scammer manipulating one target
   turn-by-turn. The reply-numbering below preserves order (useful as
   weak signal) but deliberately avoids "turn" language and tells the
   model explicitly not to assume a single continuous exchange.
   Specifically need to check the rationale field for cases where
   it seems to be connecting unrelated people into one story.

VALIDATE. Manually cross-annotate a random sample (suggest n=50-100)
   before reporting any numbers or treating labels as ground truth.
"""

import os
import sys
import json
import time
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
INPUT_CSV = "darkgram_translated.csv"
OUTPUT_CSV = "darkgram_scam_classified.csv"                  # full annotated output
FILTERED_OUTPUT_CSV = "darkgram_scam_and_potential_scam.csv"  # scam + potential_scam only
MODEL = "gpt-4.1-mini-2025-04-14"
CHECKPOINT_EVERY = 10
REQUEST_DELAY_SECONDS = 0.1

load_dotenv()
api_key = os.getenv("ELM_API_KEY")
if not api_key:
    sys.exit(
        "ELM_API_KEY not found in environment. Check .env file "
        "is in the project root and contains ELM_API_KEY=..."
    )

client = OpenAI(api_key=api_key, base_url="https://api.openai.com/v1")

# ---------------------------------------------------------------------------
# OPERATIONAL DEFINITION (PROPOSED - see caveat 1)
# ---------------------------------------------------------------------------
CLASSIFICATION_PROMPT = """You are assisting an academic dissertation study (University of Edinburgh, LLM benchmarking research) that categorizes online marketplace conversations from a Telegram scam-adjacent dataset, for research classification purposes only.

Label definitions:
- "scam": deceptive intent is clearly present -- e.g. seller demands payment with no recourse, uses fake vouches/reviews, disappears after payment, or does not deliver what was promised.
- "potential_scam": the thread does NOT confirm an actual scam occurred, but displays one or more recognized manipulation tactics (see below) that could plausibly develop into a scam if the conversation continued.
- "illicit_not_scam": the good/service is illegal or against platform rules (e.g. pirated software, blackhat tools, follower/account sales) but IS actually delivered/exchanged as advertised, with no manipulation tactics beyond a normal transaction.
- "unclear": not enough signal in the thread to decide.

Manipulation tactics to check for (tag ALL that apply, across the whole thread, even if label is not "scam"):
- "authority": claims of special access, credentials, insider status, or authority to pressure compliance (e.g. "verified seller", "official reseller", impersonating staff/admin).
- "urgency": artificial time pressure or scarcity (e.g. "offer ends today", "only 2 left", "reply now or lose your spot").
- "trust_building": unverifiable vouches, fake reviews, appeals to reputation, "trust me bro" style language, or claims of a long track record with no evidence.
- "fear_induction": threats, warnings of loss/punishment/exposure, or pressure through fear (e.g. "you'll get banned if you don't pay now", "everyone else already lost their spot").

Below is the thread: the original post followed by its replies in the order they appear in the data. IMPORTANT: replies often come from different, unrelated commenters on a public channel post, not a single continuous back-and-forth between one scammer and one target -- do not invent a narrative connecting unrelated commenters. Judge the thread as a whole, using order only as weak supporting signal (e.g. whether complaints appear after an offer), not as proof of a single ongoing exchange.

Category: {category}

{conversation}

Respond with ONLY valid JSON, no markdown formatting, in exactly this schema:
{{"label": "scam" | "potential_scam" | "illicit_not_scam" | "unclear", "confidence": <float 0-1>, "tactics": ["authority", "urgency", "trust_building", "fear_induction"] (empty list if none), "rationale": "<one sentence, max 25 words>"}}
"""


def build_conversation_text(message, replies, max_chars=4000):
    """Merge the original post and its replies into a single ordered block.
    Deliberately avoids "turn" language (see caveat 3) - labeled as numbered
    replies, not dialogue turns, since order is preserved but a single
    continuous exchange is NOT assumed."""
    message = "" if pd.isna(message) else str(message)
    replies = "" if pd.isna(replies) else str(replies)

    lines = [f"Original post: {message}"]
    if replies.strip():
        for i, reply in enumerate(replies.split("||"), start=1):
            reply = reply.strip()
            if reply:
                lines.append(f"Reply {i} (order preserved, may be a different commenter): {reply}")

    text = "\n".join(lines)
    return text[:max_chars]


def classify_row(category, message, replies, client_fn=None):
    """client_fn is injectable for dry-run testing without hitting the real API."""
    conversation = build_conversation_text(message, replies)
    prompt = CLASSIFICATION_PROMPT.format(
        category=category,
        conversation=conversation,
    )
    if client_fn is not None:
        raw = client_fn(prompt)
    else:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        raw = resp.choices[0].message.content.strip()
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {
            "label": "unclear", "confidence": 0.0, "tactics": [],
            "rationale": f"PARSE_ERROR: {raw[:200]}",
        }
    return parsed


# ---------------------------------------------------------------------------
# MAIN PIPELINE - resumable via dataframe row index
# ---------------------------------------------------------------------------
def main(client_fn=None, limit=None):
    df = pd.read_csv(INPUT_CSV)
    if limit:
        df = df.head(limit)

    if os.path.exists(OUTPUT_CSV):
        done = pd.read_csv(OUTPUT_CSV)
        done_idx = set(done["row_index"]) if "row_index" in done.columns else set()
    else:
        done = pd.DataFrame()
        done_idx = set()

    df["_effective_message"] = df["Message_Translated"].combine_first(df["Message"])
    df["_effective_replies"] = df["Combined_Replies_Translated"].combine_first(df["Combined Replies"])
    msg_col = "_effective_message"
    reply_col = "_effective_replies"

    results = []
    for idx, row in df.iterrows():
        if idx in done_idx:
            continue

        llm_result = classify_row(
            row.get("Category", ""), row.get(msg_col, ""), row.get(reply_col, ""),
            client_fn=client_fn,
        )

        results.append({
            "row_index": idx,
            "Post ID": row.get("Post ID"),
            "Category": row.get("Category"),
            "llm_label": llm_result.get("label"),
            "llm_confidence": llm_result.get("confidence"),
            "llm_tactics": ";".join(llm_result.get("tactics", [])),
            "llm_rationale": llm_result.get("rationale"),
        })

        if len(results) % CHECKPOINT_EVERY == 0:
            pd.concat([done, pd.DataFrame(results)], ignore_index=True).to_csv(OUTPUT_CSV, index=False)
            print(f"Checkpoint saved at row {idx}")

        if client_fn is None:
            time.sleep(REQUEST_DELAY_SECONDS)

    full = pd.concat([done, pd.DataFrame(results)], ignore_index=True)
    full.to_csv(OUTPUT_CSV, index=False)
    print(f"Done. Full annotated output written to {OUTPUT_CSV} ({len(full)} rows)")

    # Merge back with original data so the filtered CSV has full thread content, not just labels
    orig = pd.read_csv(INPUT_CSV)
    orig["row_index"] = orig.index
    label_cols = ["row_index", "llm_label", "llm_confidence", "llm_tactics", "llm_rationale"]
    merged = orig.merge(full[label_cols], on="row_index")
    filtered = merged[merged["llm_label"].isin(["scam", "potential_scam"])]
    filtered.to_csv(FILTERED_OUTPUT_CSV, index=False)
    print(f"Filtered scam + potential_scam output written to {FILTERED_OUTPUT_CSV} ({len(filtered)} rows)")


if __name__ == "__main__":
    main()