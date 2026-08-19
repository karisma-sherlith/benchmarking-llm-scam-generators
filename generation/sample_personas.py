"""
This file builds the sample personas.
2 (sex) x 3(age brackets) x 2 (agreeableness level) = 12 person
factorial sample from the Nemotron US Extended file.

Age Brackets: 18-30 , 31-50, 51-70+
Agreeableness: only extremes very-low+low and high+very-high
excluding average for 2 clean groups
1 persona sampled per cell, fixed random seed.
"""

import pandas as pd

FILE_PATH = r"C:\Users\DELL\.data-designer\managed-assets\datasets\en_US.parquet"
RANDOM_SEED = 42

FILTER_COLUMNS = ["uuid", "sex", "age", "agreeableness"]

print("Loading filter columns...")
df = pd.read_parquet(FILE_PATH, columns=FILTER_COLUMNS)
print(f"Total personas in dataset: {len(df)}")
print()
print("Unique sex values found: ", df["sex"].unique())
print()

def age_bracket(age):
    if 18<= age <= 30:
        return "18-30"
    elif 31<= age <= 50:
        return "31-50"
    elif age >=51:
        return "51-70+"
    else:
        return None

def agreeableness_bucket(a):
    label = a.get("label") if isinstance(a,dict) else None
    if label in ("very low", "low"):
        return "low"
    elif label in ("very high", "high"):
        return "high"
    else:
        return None
    
df["age_bracket"] = df["age"].apply(age_bracket)
df["agreeableness_bucket"] = df["agreeableness"].apply(agreeableness_bucket)

filtered = df.dropna(subset=["age_bracket", "agreeableness_bucket"])
print(f"Personas remaining after filtering and grouping: {len(filtered)} (out of {len(df)})")
print()

cell_counts = filtered.groupby(["sex","age_bracket","agreeableness_bucket"]).size()
print("Pool size per combination (before sampling):")
print(cell_counts)
print()

sampled_uuids = []
for (sex,age,agree), group in filtered.groupby(["sex","age_bracket","agreeableness_bucket"]):
    if len(group) == 0:
        print(f"WARNING: no personas found for {sex}, {age}, {agree} - this cell will be missing")
        continue
    pick = group.sample(n=1, random_state=RANDOM_SEED)
    sampled_uuids.append(pick["uuid"].values[0])

print(f"\nSelected {len(sampled_uuids)} persona UUIDS")
full_df = pd.read_parquet(FILE_PATH)
selected = full_df[full_df["uuid"].isin(sampled_uuids)].copy()

output_path = "persona_sample_12.csv"
selected.to_csv(output_path, index=False)

print(f"\nSaved {len(selected)} full persona profiles to {output_path}")