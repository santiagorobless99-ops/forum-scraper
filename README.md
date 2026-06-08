# rozed-scraper

A Selenium-based scraper and multi-format export pipeline for collecting research data from [Rozed](https://rozed.pro), an Argentine imageboard modelled after 4chan.

## About Rozed

Rozed is one of Argentina's most active imageboards, operating on an anonymous posting model structurally similar to 4chan. It hosts boards ranging from politics and news to entertainment and technology. Its anonymity and low moderation make it a significant site for the circulation of far-right, conspiratorial, and extremist content within the Argentine digital sphere, and a relevant empirical object for computational research on online radicalisation.

## Research context

This pipeline was developed for **Article 4** of a doctoral thesis by compendium on the far right in the algorithmic platform ecosystem (Spain and Argentina):

> *"Decoding digital radicalisation: A framework for the extraction and analysis of political slang in far-right online communities"*

The article proposes and validates the **CRES framework** (Contextualized Relative Extraction of Slang) — a three-phase methodology (strategic preprocessing → relative quantification → GSDMM contextual modelling) for extracting and interpreting in-group political slang from imageboards. The Rozed dataset (10,000 threads) serves as the empirical case.

## Pipeline

```
scraper_rozed.py
    └─ rozed_dataset_masivo.json        (not included — see Data availability)
         ├─ json_to_csv_spss.py    →    rozed_dataset_spss.csv
         ├─ json_to_sav.py         →    rozed_dataset_spss.sav
         └─ json_to_maxqda.py      →    maxqda_rozed/  (one .txt per thread, by board)
```

| Script | Description |
|---|---|
| `scraper_rozed.py` | Two-phase scraper: infinite scroll to harvest thread URLs, then sequential download of each thread's text and images via Selenium. Supports resuming interrupted runs. |
| `json_to_csv_spss.py` | Converts the JSON dataset to a flat CSV (UTF-8 BOM) ready for SPSS or Excel. One row per post. |
| `json_to_sav.py` | Converts the JSON dataset directly to a native SPSS `.sav` file using `pyreadstat`, with variable and value labels. |
| `json_to_maxqda.py` | Exports each thread as a plain-text document organised into subfolders by board, structured for import into MAXQDA. |
| `validate_sav.py` | Integrity check: compares row counts, thread IDs, and spot-checks text content between the source JSON and the generated SAV. |
| `check_csv.py` | Validates the generated CSV for internal newlines that would break SPSS imports. |
| `find_empty.py` | Reports posts that become empty after text cleaning, useful for dataset auditing. |
| `debug.py` | Early-stage prototype using `cloudscraper` to probe the board's HTML structure before switching to the Selenium approach. |

## Output schema

All export scripts produce the same flat structure (one row per post):

| Field | Type | Description |
|---|---|---|
| `thread_id` | string | Unique thread identifier |
| `thread_url` | string | Thread URL |
| `thread_title` | string | First 200 chars of the cleaned OP text |
| `board` | string | Board/subforum name as it appears on the site |
| `board_num` | integer | Numeric encoding of the board |
| `message_num` | integer | Position within the thread (1 = OP) |
| `is_op` | binary | 1 if original post, 0 if reply |
| `text` | string | Cleaned message text |
| `text_length` | integer | Character count |
| `word_count` | integer | Word count |
| `has_image` | binary | 1 if the thread contains at least one image |
| `image_count` | integer | Total images in the thread |
| `reply_count` | integer | Total replies (excluding OP) |

## Requirements

```
selenium
webdriver-manager
pyreadstat
pandas
beautifulsoup4
cloudscraper
```

```bash
pip install selenium webdriver-manager pyreadstat pandas beautifulsoup4 cloudscraper
```

Chrome and ChromeDriver are managed automatically by `webdriver-manager`.

## Usage

**Step 1 — Collect threads:**
```bash
python scraper_rozed.py
```
Produces `rozed_dataset_masivo.json`. The scraper saves progress every 20 threads and can resume if interrupted.

**Step 2 — Export to your preferred format:**
```bash
python json_to_csv_spss.py   # → rozed_dataset_spss.csv
python json_to_sav.py        # → rozed_dataset_spss.sav
python json_to_maxqda.py     # → maxqda_rozed/
```

**Step 3 — Validate output (optional):**
```bash
python validate_sav.py
python check_csv.py
```

## Data availability

The collected dataset is **not included** in this repository due to the sensitive nature of the content and privacy considerations. The scripts are published to document the methodological pipeline and enable replication with independently collected data.

## License
