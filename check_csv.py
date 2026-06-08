import sys
import csv

sys.stdout.reconfigure(encoding='utf-8')

INPUT_FILE = 'rozed_dataset_spss.csv'

with open(INPUT_FILE, encoding='utf-8-sig', newline='') as f:
    reader = csv.reader(f)
    rows = list(reader)

data_rows = len(rows) - 1
print(f"Total rows (including header): {len(rows)}")
print(f"Data rows                    : {data_rows}")

# Check for internal newlines — these break SPSS string field imports
newline_fields = []
for i, row in enumerate(rows[1:], start=2):
    for j, field in enumerate(row):
        if '\n' in field or '\r' in field:
            newline_fields.append((i, j, repr(field[:80])))

print(f"\nFields with internal newlines: {len(newline_fields)}")
if newline_fields:
    for item in newline_fields[:5]:
        print(f"  Row {item[0]}, Col {item[1]}: {item[2]}")
