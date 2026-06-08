"""
json_to_csv_spss.py
Converts rozed_dataset_masivo.json to a CSV suitable for analysis in SPSS.

Output CSV schema (one row per post/reply):
  - thread_id    : Unique thread identifier
  - thread_url   : Thread URL
  - thread_title : Title extracted from the OP text (first 200 chars)
  - board        : Board/subforum name extracted from the first post
  - board_num    : Numeric code for the board (for SPSS variable encoding)
  - message_num  : Position of the message within the thread (1 = OP)
  - is_op        : 1 if original post, 0 if reply
  - text         : Cleaned message text
  - text_length  : Character count of the text
  - word_count   : Word count of the text
  - has_image    : 1 if the thread contains at least one image, 0 otherwise
  - image_count  : Total number of images attached to the thread
  - reply_count  : Total number of replies (excluding the OP)
"""

import json
import csv
import re
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────
INPUT_FILE  = Path("rozed_dataset_masivo.json")
OUTPUT_FILE = Path("rozed_dataset_spss.csv")
ENCODING    = "utf-8-sig"  # BOM makes the file auto-detected correctly in SPSS/Excel

# Regex to extract the board name from the OP header
# Example: "Rozed /Inteligencia Artificial\nSEG\nFAV..."
BOARD_PATTERN = re.compile(r"Rozed\s*/([^\n]+)", re.IGNORECASE)

# UI action tags injected by the Rozed frontend (SEG=follow, FAV=favourite, etc.)
HEADER_TAGS = re.compile(
    r"^(?:SEG|FAV|HIDE|DENUNCIAR|FOLLOW|COMPARTIR)\s*\n",
    re.MULTILINE
)
TIMESTAMP = re.compile(r"^\d+[\s]*(s|m|h|d|sem|min|seg|hr?s?)\b.*\n", re.MULTILINE)
HTML_TAGS = re.compile(r"<[^>]+>")
QUOTE_SEP = re.compile(r">>(\w+)")

# Board names as they appear on the forum, mapped to a numeric code
# (ordered by descending frequency in the collected dataset)
BOARD_CODES = {
    "Política"                    : 1,
    "Anime y Manga"               : 2,
    "Morfi"                       : 3,
    "Lugares e idiomas"           : 4,
    "Conspiraciones"              : 5,
    "Reinas"                      : 6,
    "Jewtubers"                   : 7,
    "Noticias"                    : 8,
    "Rozed"                       : 9,
    "Espacio Rozero"              : 10,
    "Juegubis"                    : 11,
    "Deportes"                    : 12,
    "Normis"                      : 13,
    "Avatarfags"                  : 14,
    "Videos"                      : 15,
    "Música"                      : 16,
    "General"                     : 17,
    "Humor"                       : 18,
    "Cine y TV"                   : 19,
    "Economía"                    : 20,
    "Virgo historias y Anécdotas" : 21,
    "Preguntas"                   : 22,
    "Salud"                       : 23,
    "Tecnología"                  : 24,
    "Espiritualidad y Religion"   : 25,
    "Historia y Filosofia"        : 26,
    "Fitness"                     : 27,
    "Paranormal"                  : 28,
    "Timba"                       : 29,
    "Moda"                        : 30,
    "Guerra"                      : 31,
    "Literatura y comics"         : 32,
    "Inteligencia Artificial"     : 33,
    "Naturaleza"                  : 34,
    "Asiáticas SFW"               : 35,
    "Hágalo usted mismo"          : 36,
    "Autito brum brum"            : 37,
    "Ciencia"                     : 38,
    "Arte"                        : 39,
    "Descargas"                   : 40,
    "Programación"                : 41,
    "Umitas"                      : 42,
    "Pelotero"                    : 43,
    "Hentai"                      : 44,
}


def extract_board(text: str) -> str:
    """Extract the board name from the OP header text."""
    m = BOARD_PATTERN.search(text)
    return m.group(1).strip() if m else ""


def clean_text(text: str) -> str:
    """Strip Rozed UI metadata from a post and normalise the text for analysis."""
    text = HTML_TAGS.sub("", text)
    text = BOARD_PATTERN.sub("", text)
    text = HEADER_TAGS.sub("", text)
    text = TIMESTAMP.sub("", text)
    text = QUOTE_SEP.sub(r"@\1", text)
    text = text.strip()
    # SPSS does not support multi-line string fields; collapse newlines to " | "
    text = text.replace("\n", " | ").replace("\r", "")
    text = re.sub(r"(\s*\|\s*){2,}", " | ", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text


def count_words(text: str) -> int:
    return len(text.split()) if text else 0


def main():
    print(f"[INFO] Reading {INPUT_FILE} ...")
    with INPUT_FILE.open(encoding="utf-8") as f:
        data = json.load(f)

    print(f"[INFO] {len(data):,} threads found.")

    fieldnames = [
        "thread_id",
        "thread_url",
        "thread_title",
        "board",
        "board_num",
        "message_num",
        "is_op",
        "text",
        "text_length",
        "word_count",
        "has_image",
        "image_count",
        "reply_count",
    ]

    rows_written = 0
    empty_threads = 0

    with OUTPUT_FILE.open("w", newline="", encoding=ENCODING) as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=fieldnames,
            quoting=csv.QUOTE_NONNUMERIC,  # Strings quoted; numbers unquoted for SPSS auto-detection
        )
        writer.writeheader()

        for thread in data:
            thread_id  = thread.get("id", "")
            thread_url = thread.get("url", "")
            content    = thread.get("contenido", [])
            images     = thread.get("imagenes", [])

            image_count = len(images)
            has_image   = 1 if image_count > 0 else 0
            reply_count = max(0, len(content) - 1)

            if not content:
                empty_threads += 1
                continue

            board        = extract_board(content[0])
            thread_title = clean_text(content[0])[:200] or "(no text)"

            for idx, raw_message in enumerate(content):
                text = clean_text(raw_message)
                writer.writerow({
                    "thread_id"    : thread_id,
                    "thread_url"   : thread_url,
                    "thread_title" : thread_title,
                    "board"        : board,
                    "board_num"    : BOARD_CODES.get(board, 0),
                    "message_num"  : idx + 1,
                    "is_op"        : 1 if idx == 0 else 0,
                    "text"         : text,
                    "text_length"  : len(text),
                    "word_count"   : count_words(text),
                    "has_image"    : has_image,
                    "image_count"  : image_count,
                    "reply_count"  : reply_count,
                })
                rows_written += 1

    print(f"[OK]   CSV written -> {OUTPUT_FILE.resolve()}")
    print(f"       Rows written  : {rows_written:,}")
    print(f"       Empty threads : {empty_threads:,}")
    print(f"       Encoding      : {ENCODING} (SPSS/Excel compatible)")


if __name__ == "__main__":
    main()
