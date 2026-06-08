import json
import re
from pathlib import Path

INPUT_FILE = Path("rozed_dataset_masivo.json")
OUTPUT_DIR = Path("maxqda_rozed")

HEADER_PATTERN = re.compile(
    r"^Rozed /(.+?)\nSEG\nFAV\nHIDE\nDENUNCIAR\n(\d+\s*[dhM])\n?([\s\S]*)$"
)


def sanitize_foldername(name):
    """Remove characters that are invalid in Windows folder names."""
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()


def parse_op(first_content):
    """Extract board, timestamp, and OP body from the first post element."""
    match = HEADER_PATTERN.match(first_content)
    if match:
        board     = match.group(1).strip()
        timestamp = match.group(2).strip()
        op_text   = match.group(3).strip()
        return board, timestamp, op_text
    # Fallback: extract board and timestamp separately
    board_match     = re.match(r"^Rozed /(.+?)\n", first_content)
    timestamp_match = re.search(r"DENUNCIAR\n(\d+\s*[dhM])", first_content)
    board     = board_match.group(1).strip() if board_match else "Unknown"
    timestamp = timestamp_match.group(1).strip() if timestamp_match else ""
    return board, timestamp, ""


def build_document(thread):
    """Build the full text of a MAXQDA document for a single thread."""
    tid     = thread["id"]
    url     = thread["url"]
    title   = thread.get("titulo", "").strip()
    images  = thread.get("imagenes", [])
    content = thread.get("contenido", [])

    lines = []

    # Metadata header
    lines.append(f"ID: {tid}")
    lines.append(f"URL: {url}")

    if content:
        board, timestamp, op_text = parse_op(content[0])
        lines.append(f"Board: {board}")
        lines.append(f"Timestamp: {timestamp}")
    else:
        board    = None
        op_text  = ""
        lines.append("Board: [no data]")
        lines.append("Timestamp: [no data]")

    if title:
        lines.append(f"Title: {title}")

    lines.append(f"Attached images: {len(images)}")
    lines.append(f"Reply count: {len(content) - 1 if content else 0}")
    lines.append("")
    lines.append("=" * 60)
    lines.append("")

    # Posts
    if not content:
        lines.append("[Thread with no text — image only]")
    else:
        lines.append("ORIGINAL POST")
        lines.append("-" * 40)
        lines.append(op_text if op_text else "[Post with no text — image only]")
        lines.append("")

        for i, reply in enumerate(content[1:], start=1):
            lines.append(f"REPLY {i}")
            lines.append("-" * 40)
            lines.append(reply.strip())
            lines.append("")

    return board, "\n".join(lines)


def main():
    with open(INPUT_FILE, encoding="utf-8") as f:
        data = json.load(f)

    stats = {"total": len(data), "empty_threads": 0}
    board_counts = {}

    for thread in data:
        board, doc_text = build_document(thread)

        if board is None:
            folder_name = "_No_content"
            stats["empty_threads"] += 1
        else:
            folder_name = sanitize_foldername(board)

        board_counts[folder_name] = board_counts.get(folder_name, 0) + 1

        board_dir = OUTPUT_DIR / folder_name
        board_dir.mkdir(parents=True, exist_ok=True)

        (board_dir / f"{thread['id']}.txt").write_text(doc_text, encoding="utf-8")

    print(f"Conversion complete.")
    print(f"  Total threads processed : {stats['total']}")
    print(f"  Empty threads           : {stats['empty_threads']}")
    print(f"\nDocuments per MAXQDA group/folder:")
    for folder, count in sorted(board_counts.items()):
        print(f"  {folder}: {count}")


if __name__ == "__main__":
    main()
