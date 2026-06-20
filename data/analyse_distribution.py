import pandas as pd
from langdetect import detect, LangDetectException
from langdetect import DetectorFactory
import matplotlib.pyplot as plt
import os

DetectorFactory.seed = 0

df = pd.read_csv("darkgram_threads.csv")

# THREAD COUNT PER CHANNEL
print ("------------Thread Per Channel------------")
channel_counts = df["Channel Name"].value_counts()
print(channel_counts.to_string())
print(f"\nTotal Distinct Channels: {df['Channel Name'].nunique()}")

# REPLY LENGTH DISTRIBUTION
df["reply_length"] = df["Combined Replies"].fillna("").astype(str).str.len()
print ("\n------------Reply Length Distribution (characters)------------")
print(df["reply_length"].describe())

bins = [0,100,500,1000,3000,10000,float("inf")]
labels = ["0-100","101-500","501-1000","1001-3000","3001-10000","10000+"]
df["reply_length_bucket"] = pd.cut(df["reply_length"],bins=bins, labels=labels)
print(df["reply_length_bucket"].value_counts().sort_index())

# LANGUAGE DETECTION
def detect_language(text):
    try:
        if not isinstance(text,str) or text.strip() == "":
            return "unknown"
        return detect(text)
    except LangDetectException:
        return "unknown"
print("\n----Running Language Detection (this may take a minute)---")
df["lang_message"] = df["Message"].apply(detect_language)
df["lang_replies"] = df["Combined Replies"].apply(detect_language)

df["lang"] = df["lang_replies"].where(df["lang_replies"] != "unknown", df["lang_message"])

print("\nLanguage Distribution (all threads):")
lang_counts = df["lang"].value_counts()
print(lang_counts.to_string())

total = len(df)
hindi_count = (df["lang"] == "hi").sum()
print(f"\nEstimated Hindi Threads: {hindi_count}/{total} ({100 * hindi_count/total:.1f}%)")

df.to_csv("darkgram_threads_annotated.csv", index=False)
print("\nAnnotated CSV saved as darkgram_threads_annotated.csv")