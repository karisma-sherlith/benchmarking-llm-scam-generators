"""
Translates non-English content in darkgram_threads_annotated.csv using the
ELM API (OpenAI-compatible, GPT 4.1 Mini).

WHAT THIS SCRIPT DOES:
1. Reads darkgram_threads_annotated.csv
2. For each thread flagged purely_english == 'no':
   - Checks the Message field — if non-English, translates it
   - Splits Combined Replies on '||', checks each reply individually —
     only translates the ones that are actually non-English
3. Writes darkgram_translated.csv with all original columns plus:
   - Message_Translated
   - Combined_Replies_Translated
4. Saves progress after every row, so if the script stops partway
   (network issue, rate limit, manual interrupt) we can re-run it and
   it will skip rows already completed rather than re-translating
   (and re-paying for) them.
   pip install openai python-dotenv pandas

Based on the reply-level language detection run earlier, this should make
roughly 440 (messages) + ~1,528 (flagged replies) = ~1,968 API calls.
This is an estimate from the detection step, not a hard cap — the
detection logic in this script runs fresh, so the exact count may vary
slightly.
"""

import os
import re
import csv
import time
import sys

# ---- Dependency checks ----
try:
    import pandas as pd
except ImportError:
    sys.exit("Missing dependency: run `pip install pandas` first.")

try:
    from dotenv import load_dotenv
except ImportError:
    sys.exit("Missing dependency: run `pip install python-dotenv` first.")

try:
    from openai import OpenAI
except ImportError:
    sys.exit("Missing dependency: run `pip install openai` first.")


# ============================================================
# CONFIG — adjust these paths/settings as needed
# ============================================================
INPUT_CSV = "darkgram_threads_annotated.csv"
OUTPUT_CSV = "darkgram_translated.csv"
MODEL_NAME = "gpt-4.1-mini-2025-04-14" # from OpenAI dashboard
API_BASE_URL = "https://api.openai.com/v1"
SAVE_EVERY_N_ROWS = 1  # write progress to disk after every row processed

# ---- TEST MODE ----
# Set TEST_MODE = True to only process a small number of non-English rows.
# To sanity-check the model name, API connection, and translation
# quality BEFORE running the full ~440-row batch and spending the full
# ~1,968 API calls.
TEST_MODE = False
TEST_MODE_ROW_LIMIT = 5  # number of non-English threads to process in test mode

# When TEST_MODE is on, output goes to a separate file so it never
# overwrites or interferes with your real darkgram_translated.csv run.
if TEST_MODE:
    OUTPUT_CSV = "darkgram_translated_TEST.csv"


# ============================================================
# LANGUAGE DETECTION — reused from previous code
# ============================================================
HINDI_ROMAN_WORDS = {
    'bhai','yaar','hai','hain','hoon','kya','nahi','nhi','theek','thik',
    'aur','mera','meri','tera','teri','uska','uski','karo','kro','kar',
    'dikhra','dikhta','dikhna','dekho','dekh','bata','batao','lelo','lena','dena',
    'mai','main','mujhe','mujhko','hume','humko','tujhe','tum','aap','woh',
    'waha','yaha','yeh','ye','voh','accha','achha','sahi','galat','bilkul',
    'zaroor','abhi','kal','aaj','pehle','baad','phir','fir','toh','kyun',
    'kyunki','kaise','kaisa','kitna','kitne','kab','kahan','haa','haan',
    'ji','jee','paisa','paise','kaam','iska','iski','bhejo','bhej','karke',
    'karta','karti','raha','rahi','rhe','rahe','rahega','chahiye','hua',
    'hui','hue','tha','thi','aata','aati','aao','aaja','dost','sab','kuch',
    'koi','kaafi','bahut','thoda','jyada','kam','matlab','samjha','samjhe',
    'samjho','pata','pta','dikha','dikho','dikh','nai','ni','bol','bolo',
    'bola','boli','kr','krna','krdo','krke','apna','apni','apne',
    'laga','lagta','lagti','mila','mile','mili','sun','suno','ruk','ruko',
    'padh','cv','nhi','nai','dikhra',
}

SCRIPT_CHECKS = [
    (re.compile(u'[ऀ-ॿ]'),          'Hindi (Devanagari)'),
    (re.compile(u'[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]'), 'Urdu/Arabic/Persian'),
    (re.compile(u'[一-鿿㐀-䶿豈-﫿]'), 'Chinese'),
    (re.compile(u'[぀-ゟ]'),           'Japanese'),
    (re.compile(u'[゠-ヿ]'),           'Japanese'),
    (re.compile(u'[가-힯ᄀ-ᇿ]'), 'Korean'),
    (re.compile(u'[Ѐ-ӿ]'),           'Russian/Cyrillic'),
    (re.compile(u'[฀-๿]'),           'Thai'),
    (re.compile(u'[ঀ-৿]'),           'Bengali'),
    (re.compile(u'[઀-૿]'),           'Gujarati'),
    (re.compile(u'[ఀ-౿]'),           'Telugu'),
    (re.compile(u'[஀-௿]'),           'Tamil'),
    (re.compile(u'[ಀ-೿]'),           'Kannada'),
    (re.compile(u'[଀-୿]'),           'Odia'),
]

def has_romanized_hindi(text):
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    matches = sum(1 for w in words if w in HINDI_ROMAN_WORDS)
    return matches >= 2

def is_non_english(text):
    """Returns True if the text appears to contain non-English content,
    using the same logic as the existing annotation script."""
    if not text or not text.strip():
        return False
    for pattern, _label in SCRIPT_CHECKS:
        if pattern.search(text):
            return True
    if has_romanized_hindi(text):
        return True
    return False


# ============================================================
# TRANSLATION CALL
# ============================================================
def translate_text(client, text, retries=3):
    """Calls the ELM/OpenAI API to translate text to English.
    Retries on transient failure. Raises on persistent failure so the
    calling code can decide how to handle it (e.g. skip and log)."""
    if not text or not text.strip():
        return text

    prompt = (
        "Translate the following text to English. "
        "Preserve the original meaning and tone as closely as possible. "
        "If the text is already in English, or contains placeholder tags "
        "like <PERSON>, return it unchanged except for translating any "
        "non-English words. Return ONLY the translated text, with no "
        "explanation, preamble, or quotation marks.\n\n"
        f"Text: {text}"
    )

    last_error = None
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            last_error = e
            wait = 2 ** attempt  # simple backoff: 1s, 2s, 4s
            print(f"    [retry {attempt+1}/{retries}] API error: {e} — waiting {wait}s")
            time.sleep(wait)

    # If we get here, all retries failed.
    raise RuntimeError(f"Translation failed after {retries} attempts: {last_error}")


def translate_combined_replies(client, combined_replies):
    """Splits on '||', translates only the replies flagged as non-English,
    leaves already-English replies untouched, rejoins with '||'."""
    if not combined_replies or not combined_replies.strip():
        return combined_replies

    segments = combined_replies.split('||')
    translated_segments = []

    for seg in segments:
        stripped = seg.strip()
        if is_non_english(stripped):
            translated = translate_text(client, stripped)
            translated_segments.append(translated)
        else:
            translated_segments.append(seg)  # leave as-is, untouched

    return '||'.join(translated_segments)


# ============================================================
# MAIN
# ============================================================
def main():
    load_dotenv()
    api_key = os.getenv("ELM_API_KEY")
    if not api_key:
        sys.exit(
            "ELM_API_KEY not found in environment. Check .env file "
            "is in the project root and contains ELM_API_KEY=..."
        )

    client = OpenAI(api_key=api_key, base_url=API_BASE_URL)

    if not os.path.exists(INPUT_CSV):
        sys.exit(f"Input file not found: {INPUT_CSV} (check the path / working directory)")

    df = pd.read_csv(INPUT_CSV)

    # ---- TEST MODE: keep all English rows untouched, but only keep the
    # first TEST_MODE_ROW_LIMIT non-English rows so the rest of the script
    # (which only acts on purely_english == 'no' rows) processes a small set ----
    if TEST_MODE:
        non_eng_mask = df['purely_english'] == 'no'
        non_eng_subset = df[non_eng_mask].head(TEST_MODE_ROW_LIMIT)
        eng_subset = df[~non_eng_mask]
        df = pd.concat([eng_subset, non_eng_subset], ignore_index=True)
        print(f"TEST_MODE is ON — limiting to {TEST_MODE_ROW_LIMIT} non-English rows "
              f"(plus all already-English rows, untouched). Output: {OUTPUT_CSV}")

    # ---- Resumability: load existing output if it exists ----
    if os.path.exists(OUTPUT_CSV):
        print(f"Found existing {OUTPUT_CSV} — resuming from where it left off.")
        out_df = pd.read_csv(OUTPUT_CSV)
        # Use Post ID to track what's already done
        done_ids = set(out_df.loc[out_df['Message_Translated'].notna()])
    else:
        out_df = df.copy()
        out_df['Message_Translated'] = pd.NA
        out_df['Combined_Replies_Translated'] = pd.NA
        done_ids = set()

    total_to_process = len(out_df[out_df['purely_english'] == 'no'])
    processed_count = 0

    for idx, row in out_df.iterrows():
        if row['purely_english'] != 'no':
            continue  # only process flagged non-English threads

        if idx in done_ids:
            continue  # already done in a previous run

        processed_count += 1
        print(f"[{processed_count}/{total_to_process}] Translating row index {idx} (Post ID {row['Post ID']})...")

        try:
            message_text = row['Message'] if isinstance(row['Message'], str) else ''
            if is_non_english(message_text):
                translated_message = translate_text(client, message_text)
            else:
                translated_message = message_text

            combined_replies = row['Combined Replies'] if isinstance(row['Combined Replies'], str) else ''
            translated_replies = translate_combined_replies(client, combined_replies)

            out_df.at[idx, 'Message_Translated'] = translated_message
            out_df.at[idx, 'Combined_Replies_Translated'] = translated_replies

        except Exception as e:
            # Log and continue — don't let one failure kill the whole run.
            # This row will simply remain unmarked and get retried on next run.
            print(f"    FAILED on row index {idx} (Post ID {row['Post ID']}): {e}")
            continue

        if processed_count % SAVE_EVERY_N_ROWS == 0:
            out_df.to_csv(OUTPUT_CSV, index=False)

    # final save
    out_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nDone. Output written to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()