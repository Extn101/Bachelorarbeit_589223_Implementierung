# python
import json
import sys
from pathlib import Path

INPUT = Path("../promptset.json")
OUTPUT = Path("questions.txt")

if not INPUT.exists():
    print(f"Datei {INPUT} nicht gefunden.", file=sys.stderr)
    sys.exit(1)

with INPUT.open("r", encoding="utf-8") as f:
    data = json.load(f)

lines = []
for obj in data:
    _id = obj.get("id")
    q = obj.get("question")
    if _id is None or q is None:
        continue
    lines.append(f"{_id}: {q}")

with OUTPUT.open("w", encoding="utf-8") as out:
    out.write("\n".join(lines))

print(f"{len(lines)} Einträge nach {OUTPUT} geschrieben.")
