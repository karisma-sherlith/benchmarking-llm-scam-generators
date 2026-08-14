import json
import random
from pathlib import Path
from collections import Counter, defaultdict

INPUT_FILE = Path("conversation_relabeled_full.json")
REVIEW_FILE = Path("scammer_relabel_validation_blind_review.json")
ANSWER_KEY_FILE = Path("scammer_relabel_validation_answer_key.json")

RANDOM_SEED = 42
PER_PHASE = 8

PHASE_LABELS = ["hook", "vetting", "closure_attempt", "neutral_conversation"]
PRESSURE_LABELS = ["steady", "escalating", "de-escalating"]
TACTIC_LABELS = ["authority", "urgency", "trust_building", "fear_induction"]

LABEL_FIELDS = {"relabel_phase", "relabel_pressure", "relabel_tactics", "relabel_rationale", "relabel_retreat"}

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
    if not isinstance(turn, dict):
        return None

    if turn.get("speaker") != "scammer":
        return None
    
    phase = get_turn_label(
        turn,
        record,
        "relabel_phase"
    )

    pressure = get_turn_label(
        turn,
        record,
        "relabel_pressure"
    )

    tactics = get_turn_label(
        turn,
        record,
        "relabel_tactics"
    )

    # Only turns with both labels can be used.
    if phase not in PHASE_LABELS:
        return None

    if pressure not in PRESSURE_LABELS:
        return None

    if tactics is None:
        tactics = []

    if isinstance(tactics, str):
        tactics = [tactics]

    if not isinstance(tactics, list):
        return None

    if not all(tactic in TACTIC_LABELS for tactic in tactics):
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
        "phase": phase,
        "pressure": pressure,
        "tactics": tactics
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
        "Check where relabel_phase, relabel_pressure, relabel_tactics "
        "are stored in the JSON."
    )

print("\nLoaded:")
print(f"  Conversations/runs: {len(data):,}")
print(f"  Labeled turns:      {len(candidates):,}")

phase_counts = Counter(
    c["phase"] for c in candidates
)
pressure_counts = Counter(
    c["pressure"] for c in candidates
)

print("\nAvailable phase labels:")
for label in PHASE_LABELS:
    print(f"  {label:5s}: {phase_counts[label]:,}")
print("\nAvailable pressure labels:")
for label in PRESSURE_LABELS:
    print(f"  {label:16s}: {pressure_counts[label]:,}")

tactic_counts = Counter()
for candidate in candidates:
    for tactic in candidate["tactics"]:
        tactic_counts[tactic] += 1

print("\nAvailable tactic labels:")
for label in TACTIC_LABELS:
    print(f"    {label:20s}: {tactic_counts[label]:,}")

rng = random.Random(RANDOM_SEED)

# Shuffle first so ties are randomized reproducibly.
shuffled_candidates = candidates[:]
rng.shuffle(shuffled_candidates)

selected = []
selected_conversations = set()

phase_target = {
    label: PER_PHASE
    for label in PHASE_LABELS
}
phase_selected = Counter()

def deficits():
    return {
        label: max(
        0,
        phase_target[label]
        - phase_selected[label]
        )
        for label in PHASE_LABELS
    }

while True:
    phasee_deficit = deficits()
    if sum(phasee_deficit.values()) == 0:
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
        p_deficit = phasee_deficit[
            candidate["phase"]
        ]
        score = p_deficit ** 2
        if score > best_score:
            best_score = score
            best_candidates = [candidate]

        elif score == best_score:
            best_candidates.append(candidate)
    candidate = rng.choice(best_candidates)

    selected.append(candidate)
    selected_conversations.add(candidate["conversation_id"])

    phase_selected[
        candidate["phase"]
    ] += 1

print("\nSelected:")
print(f"  Total sampled turns: {len(selected)}")
print(
    f"  Unique conversations/runs: "
    f"{len(selected_conversations)}"
)

print("\nSampled phase:")
for label in PHASE_LABELS:
    print(
        f"  {label:22s}: "
        f"{phase_selected[label]:2d} / "
        f"{phase_target[label]}"
    )

for label in PHASE_LABELS:
    if phase_selected[label] < phase_target[label]:
        print(
            f"\nWARNING: Could only sample "
            f"{phase_selected[label]} "
            f"{label!r} phase cases."
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
        "your_phase_guess": "",
        "your_pressure_guess": "",
        "your_authority_guess": "",
        "your_urgency_guess": "",
        "your_trust_building_guess": "",
        "your_fear_induction_guess": "",
    }
    review_items.append(review_item)

    actual_tactics = set(candidate["tactics"])

    answer_key_item = {
        "review_id": review_id,
        "persona_uuid": record.get("persona_uuid"),
        "run_number": record.get("run_number"),
        "sampled_turn": candidate["turn_number"],
        "relabel_phase": candidate["phase"],
        "relabel_pressure": candidate["pressure"],
        "relabel_tactics": candidate["tactics"],
        "relabel_authority": ("yes" if "authority" in actual_tactics else "no"),
        "relabel_urgency": ("yes" if "urgency" in actual_tactics else "no"),
        "relabel_trust_building": ("yes" if "trust_building" in actual_tactics else "no"),
        "relabel_fear_induction": ("yes" if "fear_induction" in actual_tactics else "no"),
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
    if answer["relabel_phase"] not in PHASE_LABELS:
        raise RuntimeError(
            "SAFETY CHECK FAILED: invalid phase."
        )
    if answer["relabel_pressure"] not in PRESSURE_LABELS:
            raise RuntimeError(
                "SAFETY CHECK FAILED: invalid pressure."
            )
    for tactic in TACTIC_LABELS:
        binary_field = f"relabel_{tactic}"
        if answer[binary_field] not in {"yes", "no"}:
            raise RuntimeError(
                "SAFETY CHECK FAILED: invalid binary field."
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