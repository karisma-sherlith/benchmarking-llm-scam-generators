'''
According to our findings: the darkgram data folder has 2 sub folders:
Posts and Replies
Posts contain the post message from each channel from each subcategory
Replies contain folders for each channel in subcategory and each such folder has csv's
Within each csv the 1st row is the actual post message and the rows following it are the replies to that post.

So now we extract these replies to have a multi-turn conversation threads
Discard files with only 1 row which is the post message (only looking for conversation threads)
Make a single csv for all 5 categories
Post Id | Category | Channel Name | URL | Message | Combined Replies
'''

import os
import csv
import glob

REPLIES_ROOT = r"C:\Users\DELL\Desktop\UoE\Dissertation\SayakSR-DarkGram-56d2023\data\replies\replies"
OUTPUT_FILE = "darkgram_threads.csv"
REPLY_SEPARATOR = " || "

'''
File Format: {timestamp}_{post_id}_replies.csv - so we extract the post id from filename
'''
def extract_post_id_from_filename(filename):
    base = os.path.basename(filename)
    base = base.replace('_replies.csv','')
    parts = base.split('_')
    return parts[-1]

def clean_text(text):
    if not text:
        return ''
    return text.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')

'''
Read each reply csv. Return if it has more than 1 row if not none
'''
def process_csv(filepath, category, channel_name):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except Exception as e:
        print(f' [SKIP - error reading] {filepath}: {e}')
        return None
    
    if len(rows) <=1:
       return None
    
    post_row = rows[0]
    reply_rows = rows[1:]

    post_id = extract_post_id_from_filename(filepath)
    message = clean_text(post_row.get('message',''))
    url = post_row.get('URL','')

    combined_replies = REPLY_SEPARATOR.join(clean_text(r.get('message','')) for r in reply_rows if r.get('message'))

    return {
        'Post ID': post_id,
        'Category': category,
        'Channel Name': channel_name,
        'URL': url,
        'Message': message,
        'Combined Replies': combined_replies,
    }

def main():
    output_rows = []

    if not os.path.isdir(REPLIES_ROOT):
        print(f'ERROR: Path not found: {REPLIES_ROOT}')
        return
    
    categories = [
        d for d in os.listdir(REPLIES_ROOT)
        if os.path.isdir(os.path.join(REPLIES_ROOT, d))
    ]
    print(f'Found {len(categories)} categories: {categories}')

    for category in categories:
        category_path = os.path.join(REPLIES_ROOT,category)
        channels = [
            d for d in os.listdir(category_path)
            if os.path.isdir(os.path.join(category_path,d))
        ]
        print(f'\nCategory: {category} ({len(channels)} channels)')

        for channel_name in channels:
            channel_path = os.path.join(category_path,channel_name)
            csv_files = glob.glob(os.path.join(channel_path,'*_replies.csv'))

            for csv_file in csv_files:
                result = process_csv(csv_file, category, channel_name)
                if result:
                    output_rows.append(result)
        
        print(f' -> Thread with replies so far (total): {len(output_rows)}')

        if output_rows:
            fieldnames = ['Post ID', 'Category', 'Channel Name', 'URL', 'Message', 'Combined Replies']
            with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(output_rows)
            print(f'\nDone, Wrote {len(output_rows)} threads to {OUTPUT_FILE}')
        else:
            print('\nNo threads found with replies')

if __name__ == '__main__':
    main()

'''
Done, Wrote 1762 threads to darkgram_threads.csv
A small number of rows (~8-10) had malformed source data 
(row nos: 305,350,356,596,597,598,599,600,601)
where post-level fields (Post ID, Channel Name, URL, Message) 
were empty in the original CSV; these were manually corrected after export.
'''