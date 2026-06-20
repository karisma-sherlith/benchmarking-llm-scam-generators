import csv
import re

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

# All ranges as explicit Unicode escapes to avoid heredoc encoding issues
SCRIPT_CHECKS = [
    (re.compile(u'[ऀ-ॿ]'),          'Hindi (Devanagari)'),
    (re.compile(u'[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]'), 'Urdu/Arabic/Persian'),
    (re.compile(u'[一-鿿㐀-䶿豈-﫿]'), 'Chinese'),
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
    (re.compile(u'[぀-ヿㇰ-ㇿ･-ﾟ]'), 'Japanese'),
]

GARBLED_RE = re.compile(
    u'�'                              # replacement char
    u'|[​‌‍﻿]'        # zero-width chars
    u'|[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]' # control chars
    # garbled ð sequences: ð followed by chars that indicate bad UTF-8 decoding
    u'|[\xF0][\x80-\xBF]'
)

def has_garbled(text):
    if '�' in text:
        return True
    if '​' in text or '‌' in text or '‍' in text or '﻿' in text:
        return True
    if re.search(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', text):
        return True
    # garbled sequences like ð—›ð—¢ð — these appear as ð + latin extended chars
    if re.search(r'ð[^\s\w]|ð\x97|ð\x80', text):
        return True
    return False

def has_romanized_hindi(text):
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    matches = sum(1 for w in words if w in HINDI_ROMAN_WORDS)
    return matches >= 2

def annotate_row(combined_replies):
    if not combined_replies or not combined_replies.strip():
        return 'yes', '', 'yes'

    segments = [s.strip() for s in combined_replies.split('||')]

    garbled = any(has_garbled(seg) for seg in segments)
    clean_text = 'no' if garbled else 'yes'

    other_langs = set()
    all_english = True

    for seg in segments:
        if not seg:
            continue
        for pattern, label in SCRIPT_CHECKS:
            if pattern.search(seg):
                other_langs.add(label)
                all_english = False
        if has_romanized_hindi(seg):
            other_langs.add('Romanized Hindi')
            all_english = False

    purely_english = 'yes' if all_english else 'no'
    other_languages_str = ', '.join(sorted(other_langs)) if other_langs else ''
    return purely_english, other_languages_str, clean_text


input_path  = 'darkgram_threads.csv'
output_path = 'darkgram_threads_annotated.csv'

with open(input_path, 'r', encoding='utf-8', errors='replace') as infile, \
     open(output_path, 'w', encoding='utf-8', newline='') as outfile:

    reader = csv.DictReader(infile)
    fieldnames = list(reader.fieldnames) + ['purely_english', 'other_languages', 'clean_text']
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader:
        combined = row.get('Combined Replies', '')
        pe, ol, ct = annotate_row(combined)
        row['purely_english'] = pe
        row['other_languages'] = ol
        row['clean_text'] = ct
        writer.writerow(row)

print("Done!")