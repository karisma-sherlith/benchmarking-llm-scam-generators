import pandas as pd
import os

# Posts folder path
POSTS_PATH = r"C:\Users\DELL\Desktop\UoE\Dissertation\SayakSR-DarkGram-56d2023\data\posts\posts"

# Categories available in posts
categories = os.listdir(POSTS_PATH)
print("Catgeories Found:", categories)

for category in categories:
    category_path = os.path.join(POSTS_PATH,category)
    if os.path.isdir(category_path):
        files = os.listdir(category_path)
        total_posts = 0
        for file in files:
            if file.endswith('.csv'):
                df = pd.read_csv(os.path.join(category_path,file))
                total_posts += len(df)
        print(f"{category}: {len(files)} channels, {total_posts} total posts")