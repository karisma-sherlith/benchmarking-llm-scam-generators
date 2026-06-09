import pandas as pd
import os

POSTS_PATH = r"C:\Users\DELL\Desktop\UoE\Dissertation\SayakSR-DarkGram-56d2023\data\posts\posts"

# category = "social_media_manipulation"
category = "blackhat_resources"
category_path = os.path.join(POSTS_PATH, category)

# Read all CSVs in this category into one df
dfs = []
for file in os.listdir(category_path):
    if file.endswith('.csv'):
        df = pd.read_csv(os.path.join(category_path, file), low_memory=False)
        dfs.append(df)

combined = pd.concat(dfs, ignore_index=True)

print(f"Total posts in social_media_manipulation: {len(combined)}")
print(f"Columns: {combined.columns.tolist()}")
print("\n--- SAMPLE MESSAGES (first 20) ---\n")

# Print first 20 non-null messages
messages = combined['message'].dropna().head(20)
for i, msg in enumerate(messages, 1):
    print(f"[{i}] {msg[:300]}")
    print("-" * 50)