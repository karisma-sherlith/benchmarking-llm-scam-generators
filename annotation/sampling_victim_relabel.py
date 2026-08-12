import json
import random
from pathlib import Path
from collections import Counter, defaultdict

INPUT_FILE = Path("conversation_relabeled_victim.json")
REVIEW_FILE = Path("victim_relabel_validation_blind_review.json")
ANSWER_KEY_FILE = Path("victim_relabel_validation_answer_key.json")

RANDOM_SEED = 42
PER_SUSPICION = 8
PER_ENGAGEMENT = 8

SUSPICION_LABELS = ["none", "mild", "high",]
ENGAGEMENT_LABELS = ["avoidant", "neutral", "curious", "soft_compliance",]

# Explicitly excluded because there are 0 cases.
EXCLUDED_ENGAGEMENT = {"hard_compliance"}

LABEL_FIELDS = {"relabel_suspicion", "relabel_engagement", "relabel_rationale",}

def remove_labels(obj):
    if isinstance(obj, dict):
        return {
            key: remove_labels(value)
            for key, value in obj.items()
            if key not in LABEL_FIELDS
        }

    if isinstance(obj, list):
        return [remove_labels(item) for item in obj]
    return obj


def get_conversation_id(record, record_index):
    persona_uuid = record.get("persona_uuid", f"record_{record_index}")
    run_number = record.get("run_number")
    if run_number is not None:
        return f"{persona_uuid}::run_{run_number}"
    return f"{persona_uuid}::record_{record_index}"


def get_turn_label(turn, record, label_name):
    if isinstance(turn, dict) and label_name in turn:
        return turn[label_name]
    if isinstance(record, dict) and label_name in record:
        return record[label_name]
    return None


def get_turn_number(turn, fallback_index):
    if isinstance(turn, dict) and "turn" in turn:
        return turn["turn"]
    return fallback_index


def make_candidate(record, record_index, turn, turn_index):
    suspicion = get_turn_label(
        turn,
        record,
        "relabel_suspicion"
    )

    engagement = get_turn_label(
        turn,
        record,
        "relabel_engagement"
    )

    # Only turns with both labels can be used.
    if suspicion not in SUSPICION_LABELS:
        return None

    if engagement not in ENGAGEMENT_LABELS:
        return None

    conversation_id = get_conversation_id(
        record,
        record_index
    )

    return {
        "conversation_id": conversation_id,
        "record_index": record_index,
        "turn_index": turn_index,
        "turn_number": get_turn_number(turn, turn_index),

        # Ground truth is kept internally ONLY.
        "suspicion": suspicion,
        "engagement": engagement,
    }

if not INPUT_FILE.exists():
    raise FileNotFoundError("Could not find file")

with INPUT_FILE.open("r", encoding="utf-8") as f:
    data = json.load(f)

if not isinstance(data, list):
    raise ValueError("Format Error")

candidates = []

for record_index, record in enumerate(data):
    transcript = record.get("transcript")
    if not isinstance(transcript, list):
        continue
    for turn_index, turn in enumerate(transcript):
        candidate = make_candidate(
            record,
            record_index,
            turn,
            turn_index
        )
        if candidate is not None:
            candidates.append(candidate)

if not candidates:
    raise ValueError(
        "No labeled turns were found.\n"
        "Check where relabel_suspicion and relabel_engagement "
        "are stored in the JSON."
    )

print("\nLoaded:")
print(f"  Conversations/runs: {len(data):,}")
print(f"  Labeled turns:      {len(candidates):,}")

suspicion_counts = Counter(
    c["suspicion"] for c in candidates
)
engagement_counts = Counter(
    c["engagement"] for c in candidates
)
print("\nAvailable suspicion labels:")
for label in SUSPICION_LABELS:
    print(f"  {label:5s}: {suspicion_counts[label]:,}")
print("\nAvailable engagement labels:")
for label in ENGAGEMENT_LABELS:
    print(f"  {label:16s}: {engagement_counts[label]:,}")

rng = random.Random(RANDOM_SEED)

# Shuffle first so ties are randomized reproducibly.
shuffled_candidates = candidates[:]
rng.shuffle(shuffled_candidates)

selected = []
selected_conversations = set()

suspicion_target = {
    label: PER_SUSPICION
    for label in SUSPICION_LABELS
}

engagement_target = {
    label: PER_ENGAGEMENT
    for label in ENGAGEMENT_LABELS
}

suspicion_selected = Counter()
engagement_selected = Counter()


def deficits():
    return (
        {
            label: max(
                0,
                suspicion_target[label]
                - suspicion_selected[label]
            )
            for label in SUSPICION_LABELS
        },
        {
            label: max(
                0,
                engagement_target[label]
                - engagement_selected[label]
            )
            for label in ENGAGEMENT_LABELS
        }
    )

while True:
    suspicion_deficit, engagement_deficit = deficits()
    if (
        sum(suspicion_deficit.values()) == 0
        and
        sum(engagement_deficit.values()) == 0
    ):
        break
    remaining = [
        c for c in shuffled_candidates
        if c["conversation_id"] not in selected_conversations
    ]
    if not remaining:
        break

    best_score = -1
    best_candidates = []
    for candidate in remaining:
        s_deficit = suspicion_deficit[
            candidate["suspicion"]
        ]
        e_deficit = engagement_deficit[
            candidate["engagement"]
        ]
        score = (
            s_deficit ** 2
            +
            e_deficit ** 2
        )

        if score > best_score:
            best_score = score
            best_candidates = [candidate]

        elif score == best_score:
            best_candidates.append(candidate)
    candidate = rng.choice(best_candidates)

    selected.append(candidate)
    selected_conversations.add(
        candidate["conversation_id"]
    )

    suspicion_selected[
        candidate["suspicion"]
    ] += 1

    engagement_selected[
        candidate["engagement"]
    ] += 1

print("\nSelected:")
print(f"  Total sampled turns: {len(selected)}")
print(
    f"  Unique conversations/runs: "
    f"{len(selected_conversations)}"
)

print("\nSampled suspicion:")
for label in SUSPICION_LABELS:
    print(
        f"  {label:5s}: "
        f"{suspicion_selected[label]:2d} / "
        f"{suspicion_target[label]}"
    )

print("\nSampled engagement:")
for label in ENGAGEMENT_LABELS:
    print(
        f"  {label:16s}: "
        f"{engagement_selected[label]:2d} / "
        f"{engagement_target[label]}"
    )

for label in SUSPICION_LABELS:
    if suspicion_selected[label] < suspicion_target[label]:
        print(
            f"\nWARNING: Could only sample "
            f"{suspicion_selected[label]} "
            f"{label!r} suspicion cases."
        )

for label in ENGAGEMENT_LABELS:
    if engagement_selected[label] < engagement_target[label]:
        print(
            f"\nWARNING: Could only sample "
            f"{engagement_selected[label]} "
            f"{label!r} engagement cases."
        )
review_items = []
answer_key_items = []

for review_id, candidate in enumerate(
    selected,
    start=1
):
    record = data[candidate["record_index"]]
    transcript = record["transcript"]
    sampled_turn_index = candidate["turn_index"]
    context = transcript[:sampled_turn_index + 1]
    clean_context = remove_labels(context)
    review_item = {
        "review_id": review_id,
        "persona_uuid": record.get("persona_uuid"),
        "run_number": record.get("run_number"),
        "sampled_turn": candidate["turn_number"],
        "transcript": clean_context,
        "your_suspicion_guess": "",
        "your_engagement_guess": "",
    }
    review_items.append(review_item)
    answer_key_item = {
        "review_id": review_id,
        "persona_uuid": record.get("persona_uuid"),
        "run_number": record.get("run_number"),
        "sampled_turn": candidate["turn_number"],
        "relabel_suspicion": candidate["suspicion"],
        "relabel_engagement": candidate["engagement"],
    }
    answer_key_items.append(answer_key_item)

review_text = json.dumps(
    review_items,
    ensure_ascii=False
)
for forbidden_field in LABEL_FIELDS:
    if forbidden_field in review_text:
        raise RuntimeError(
            f"SAFETY CHECK FAILED: "
            f"{forbidden_field!r} leaked into the blind review."
        )
review_conversations = [
    (
        item.get("persona_uuid"),
        item.get("run_number")
    )
    for item in review_items
]

if len(review_conversations) != len(set(review_conversations)):
    raise RuntimeError(
        "SAFETY CHECK FAILED: "
        "more than one sampled turn came from the same "
        "conversation/run."
    )
for answer in answer_key_items:
    if answer["relabel_engagement"] in EXCLUDED_ENGAGEMENT:
        raise RuntimeError(
            "SAFETY CHECK FAILED: hard_compliance was sampled."
        )
with REVIEW_FILE.open("w", encoding="utf-8") as f:
    json.dump(
        review_items,
        f,
        ensure_ascii=False,
        indent=2
    )

with ANSWER_KEY_FILE.open("w", encoding="utf-8") as f:
    json.dump(
        answer_key_items,
        f,
        ensure_ascii=False,
        indent=2
    )