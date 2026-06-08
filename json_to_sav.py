"""
json_to_sav.py
Converts rozed_dataset_masivo.json directly to .sav (native SPSS format).
thread_title is set to the first 200 characters of the cleaned OP text.
"""

import json
import re
import traceback
import pyreadstat
import pandas as pd
from pathlib import Path

INPUT_FILE  = Path("rozed_dataset_masivo.json")
OUTPUT_FILE = Path("rozed_dataset_spss.sav")

# ── Cleaning patterns ──────────────────────────────────────────────────────────
BOARD_PATTERN = re.compile(r"Rozed\s*/([^\n]+)", re.IGNORECASE)
HEADER_TAGS   = re.compile(r"^(?:SEG|FAV|HIDE|DENUNCIAR|FOLLOW|COMPARTIR)\s*\n", re.MULTILINE)
TIMESTAMP     = re.compile(r"^\d+[\s]*(s|m|h|d|sem|min|seg|hr?s?)\b.*\n", re.MULTILINE)
HTML_TAGS     = re.compile(r"<[^>]+>")
QUOTE_SEP     = re.compile(r">>(\w+)")
# Control characters that cause pyreadstat to crash (excluding tab and space)
CTRL_CHARS    = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def extract_board(text: str) -> str:
    m = BOARD_PATTERN.search(text)
    return m.group(1).strip() if m else ""


def clean_text(text: str, max_len: int = 4000) -> str:
    text = HTML_TAGS.sub("", text)
    text = BOARD_PATTERN.sub("", text)
    text = HEADER_TAGS.sub("", text)
    text = TIMESTAMP.sub("", text)
    text = QUOTE_SEP.sub(r"@\1", text)
    text = text.strip()
    # Newlines collapsed to a separator — required for SPSS string field compatibility
    text = text.replace("\n", " | ").replace("\r", "")
    text = re.sub(r"(\s*\|\s*){2,}", " | ", text)
    text = CTRL_CHARS.sub("", text)
    return text[:max_len]


def count_words(text: str) -> int:
    return len(text.split()) if text else 0


print(f"[INFO] Reading {INPUT_FILE} ...")
with INPUT_FILE.open(encoding="utf-8") as f:
    data = json.load(f)

print(f"[INFO] {len(data):,} threads found. Processing...")

rows = []
for thread in data:
    content = thread.get("contenido", [])
    if not content:
        continue

    thread_id    = thread.get("id", "")
    thread_url   = thread.get("url", "")
    images       = thread.get("imagenes", [])
    image_count  = len(images)
    has_image    = 1 if image_count > 0 else 0
    reply_count  = max(0, len(content) - 1)
    board        = extract_board(content[0])
    thread_title = clean_text(content[0], max_len=200) or "(no text)"

    for idx, raw_message in enumerate(content):
        text = clean_text(raw_message, max_len=4000)
        rows.append({
            "thread_id"    : thread_id,
            "thread_url"   : thread_url,
            "thread_title" : thread_title,
            "board"        : board,
            "message_num"  : float(idx + 1),
            "is_op"        : float(1 if idx == 0 else 0),
            "text"         : text,
            "text_length"  : float(len(text)),
            "word_count"   : float(count_words(text)),
            "has_image"    : float(has_image),
            "image_count"  : float(image_count),
            "reply_count"  : float(reply_count),
        })

df = pd.DataFrame(rows)
print(f"[INFO] DataFrame: {len(df):,} rows × {len(df.columns)} columns")

for col in ["thread_id", "thread_url", "thread_title", "board", "text"]:
    df[col] = df[col].astype(object)
for col in ["message_num", "is_op", "text_length", "word_count", "has_image", "image_count", "reply_count"]:
    df[col] = df[col].astype(float)

for col in ["thread_id", "thread_url", "thread_title", "board", "text"]:
    print(f"       Max length [{col}]: {df[col].str.len().max()}")

variable_labels = {
    "thread_id"    : "Unique thread identifier",
    "thread_url"   : "Thread URL",
    "thread_title" : "OP text used as thread title (200 chars max)",
    "board"        : "Board / subforum name",
    "message_num"  : "Message position within the thread (1 = OP)",
    "is_op"        : "Is original post (1 = yes, 0 = no)",
    "text"         : "Cleaned message text",
    "text_length"  : "Text length in characters",
    "word_count"   : "Word count of the message",
    "has_image"    : "Thread contains at least one image (1 = yes, 0 = no)",
    "image_count"  : "Total images attached to the thread",
    "reply_count"  : "Total replies to the OP",
}

value_labels = {
    "is_op"     : {0.0: "Reply", 1.0: "Original post"},
    "has_image" : {0.0: "No image", 1.0: "Has image"},
}

print(f"[INFO] Writing {OUTPUT_FILE} ...")
try:
    pyreadstat.write_sav(
        df,
        str(OUTPUT_FILE),
        variable_value_labels=value_labels,
        column_labels=list(variable_labels.values()),
    )
    print(f"[OK]   SAV written -> {OUTPUT_FILE.resolve()}")
    print(f"       Rows: {len(df):,}  |  Columns: {len(df.columns)}")
except Exception as e:
    print(f"[ERROR] {e}")
    traceback.print_exc()
