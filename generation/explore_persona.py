"""
Exploring the downloaded persona before getting the sample personas.
"""

import os
import glob
import pandas as pd

DATASET_ROOT = os.path.expanduser(r"~\.data-designer\managed-assets\datasets")

# Find all parquet files under the datasets folder
parquet_files = glob.glob(os.path.join(DATASET_ROOT, "**", "*.parquet"), recursive=True)

print(f"Searched: {DATASET_ROOT}")
print(f"Found {len(parquet_files)} parquet file(s):")
for f in parquet_files:
    size_mb = os.path.getsize(f) / (1024 * 1024)
    print(f"  {f}  ({size_mb:.1f} MB)")
print()

if not parquet_files:
    print("No parquet files found. The download may use a different format")
    print("(e.g. .csv, .json, .jsonl) - check the folder manually:")
    print(f"  {DATASET_ROOT}")
else:
    # Load just the first file to check schema
    df = pd.read_parquet(parquet_files[0])

    print("Column names:", list(df.columns))
    print()
    print("Row count in this file:", len(df))
    print()
    print("First row (all fields, truncated for readability):")
    for col in df.columns:
        val = str(df.iloc[0][col])
        print(f"  {col}: {val[:150]}{'...' if len(val) > 150 else ''}")
    print()

    # Check the fields our project depends on
    print("--- Fields our sampling design needs ---")
    for field in ["sex", "age", "agreeableness", "openness", "conscientiousness",
                  "extraversion", "neuroticism", "finance_persona", "state", "city"]:
        if field in df.columns:
            print(f"  FOUND: {field}  (example: {str(df.iloc[0][field])[:100]})")
        else:
            print(f"  MISSING: {field}")