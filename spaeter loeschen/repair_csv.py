import csv
import os

INPUT_FILE = "benchmark_results_nfl.csv"
OUTPUT_FILE = "benchmark_results_nfl_fixed.csv"

def repair_csv():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Datei '{INPUT_FILE}' nicht gefunden.")
        return

    print("🛠️ Repariere CSV-Datei für Excel...")

    try:
        # 1. Einlesen mit Komma-Trennung (Standard)
        with open(INPUT_FILE, "r", encoding="utf-8") as f_in:
            reader = csv.DictReader(f_in, delimiter=",", quotechar='"')
            rows = list(reader) # Alle Daten in den Speicher laden
            fieldnames = reader.fieldnames

        # 2. Schreiben mit Semikolon-Trennung (Excel-freundlich)
        # 'utf-8-sig' hilft Excel, Umlaute (ä,ö,ü) sofort richtig zu erkennen
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()
            writer.writerows(rows)

        print(f"✅ Fertig! Die neue Datei heißt: '{OUTPUT_FILE}'")
        print("👉 Du kannst sie jetzt einfach per Doppelklick in Excel öffnen.")

    except Exception as e:
        print(f"Fehler: {e}")

if __name__ == "__main__":
    repair_csv()