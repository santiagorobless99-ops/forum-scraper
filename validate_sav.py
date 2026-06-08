"""
validate_sav.py
Compares the generated .sav file against the source JSON to verify data integrity.
"""
import json
import re
import random
import pyreadstat
import pandas as pd
from pathlib import Path

JSON_FILE = Path("rozed_dataset_masivo.json")
SAV_FILE  = Path("rozed_dataset_spss.sav")

BOARD_PATTERN = re.compile(r"Rozed\s*/([^\n]+)", re.IGNORECASE)
HEADER_TAGS   = re.compile(r"^(?:SEG|FAV|HIDE|DENUNCIAR|FOLLOW|COMPARTIR)\s*\n", re.MULTILINE)
TIMESTAMP     = re.compile(r"^\d+[\s]*(s|m|h|d|sem|min|seg|hr?s?)\b.*\n", re.MULTILINE)
HTML_TAGS     = re.compile(r"<[^>]+>")
QUOTE_SEP     = re.compile(r">>(\w+)")


def clean_text(text):
    text = HTML_TAGS.sub("", text)
    text = BOARD_PATTERN.sub("", text)
    text = HEADER_TAGS.sub("", text)
    text = TIMESTAMP.sub("", text)
    text = QUOTE_SEP.sub(r"@\1", text)
    text = text.strip()
    text = text.replace("\n", " | ")
    text = re.sub(r"(\s*\|\s*){2,}", " | ", text)
    return text


print("=" * 60)
print("DATA INTEGRITY VALIDATION: JSON → SAV")
print("=" * 60)

# ── 1. Load JSON ──────────────────────────────────────────────
print("\n[1] Loading JSON...")
with JSON_FILE.open(encoding="utf-8") as f:
    data = json.load(f)

json_threads_total = len(data)
json_threads_empty = sum(1 for h in data if not h.get("contenido"))
json_threads_valid = json_threads_total - json_threads_empty
json_messages      = sum(len(h.get("contenido", [])) for h in data if h.get("contenido"))
json_ids           = {h["id"] for h in data if h.get("contenido")}

print(f"   Total threads     : {json_threads_total:,}")
print(f"   Threads with data : {json_threads_valid:,}")
print(f"   Total messages    : {json_messages:,}")
print(f"   Unique IDs        : {len(json_ids):,}")

# ── 2. Load SAV ───────────────────────────────────────────────
print("\n[2] Loading SAV...")
df, meta = pyreadstat.read_sav(str(SAV_FILE))

sav_rows = len(df)
sav_cols = len(df.columns)
sav_ids  = set(df["thread_id"].unique())
sav_ops  = df[df["is_op"] == 1]
sav_resp = df[df["is_op"] == 0]

print(f"   Total rows        : {sav_rows:,}")
print(f"   Columns           : {sav_cols}")
print(f"   Unique IDs        : {len(sav_ids):,}")
print(f"   OP messages       : {len(sav_ops):,}")
print(f"   Replies           : {len(sav_resp):,}")

# ── 3. Checks ─────────────────────────────────────────────────
print("\n[3] Checks...")
ok = True

match_msgs = sav_rows == json_messages
print(f"   Message count matches       : {'OK' if match_msgs else 'ERROR'} ({sav_rows:,} vs {json_messages:,})")
ok = ok and match_msgs

ids_only_json = json_ids - sav_ids
ids_only_sav  = sav_ids - json_ids
match_ids = len(ids_only_json) == 0 and len(ids_only_sav) == 0
print(f"   Thread IDs match            : {'OK' if match_ids else 'ERROR'}")
if not match_ids:
    print(f"     Only in JSON: {len(ids_only_json)}")
    print(f"     Only in SAV : {len(ids_only_sav)}")
ok = ok and match_ids

match_ops = len(sav_ops) == json_threads_valid
print(f"   OP count = valid threads    : {'OK' if match_ops else 'ERROR'} ({len(sav_ops):,} vs {json_threads_valid:,})")
ok = ok and match_ops

nulls = df[["thread_id", "board", "text", "message_num", "is_op"]].isnull().sum()
has_nulls = nulls.sum() > 0
print(f"   Nulls in key columns        : {'ERROR' if has_nulls else 'OK'}")
if has_nulls:
    print(f"     {nulls[nulls > 0].to_dict()}")
ok = ok and not has_nulls

empty_texts = (df["text"].str.strip() == "").sum()
print(f"   Empty text fields           : {empty_texts:,} {'(warning)' if empty_texts > 0 else 'OK'}")

min_msg   = df.groupby("thread_id")["message_num"].min()
bad_starts = (min_msg != 1).sum()
print(f"   Threads starting at msg 1   : {'OK' if bad_starts == 0 else f'ERROR ({bad_starts} threads)'}")
ok = ok and bad_starts == 0

# ── 4. Spot-check ─────────────────────────────────────────────
print("\n[4] Spot-check (3 random threads)...")
random.seed(42)
sample_ids = random.sample(list(json_ids), 3)

for hid in sample_ids:
    json_thread = next(h for h in data if h["id"] == hid)
    json_n_msgs = len(json_thread.get("contenido", []))
    sav_n_msgs  = len(df[df["thread_id"] == hid])
    first_json  = clean_text(json_thread["contenido"][0])
    first_sav   = df[df["thread_id"] == hid].sort_values("message_num").iloc[0]["text"]
    count_match = json_n_msgs == sav_n_msgs
    text_match  = first_json == first_sav.strip()
    print(f"   Thread {hid[:12]}...")
    print(f"     Message count JSON={json_n_msgs} SAV={sav_n_msgs} -> {'OK' if count_match else 'ERROR'}")
    print(f"     OP text matches                -> {'OK' if text_match else 'DIFF'}")
    if not text_match:
        print(f"       JSON: {repr(first_json[:80])}")
        print(f"       SAV : {repr(first_sav[:80])}")
    ok = ok and count_match

print("\n" + "=" * 60)
print(f"RESULT: {'ALL CHECKS PASSED — no data loss' if ok else 'DISCREPANCIES FOUND'}")
print("=" * 60)
