import csv
import statistics
import os

# --- KONFIGURATION ---
INPUT_FILE = "benchmark_results_nfl.csv"

def print_separator(char="-", length=95):
    print(char * length)

def evaluate_benchmark():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Fehler: Datei '{INPUT_FILE}' nicht gefunden.")
        return

    # Datenstruktur: model -> { 'times': [], 'tokens': [], 'tps': [] }
    model_stats = {}

    # Für Detail-Analyse (Optional): model -> difficulty -> times
    difficulty_stats = {}

    print(f"📊 Lade Daten aus {INPUT_FILE}...\n")

    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row_count = 0

            for row in reader:
                model = row['model']
                difficulty = row.get('difficulty', 'Unknown')

                # Initialisierung
                if model not in model_stats:
                    model_stats[model] = {'times': [], 'tokens': [], 'tps': []}

                if model not in difficulty_stats:
                    difficulty_stats[model] = {}
                if difficulty not in difficulty_stats[model]:
                    difficulty_stats[model][difficulty] = []

                # Werte parsen
                try:
                    time_sec = float(row['time_sec'])
                    tokens = int(row['tokens'])

                    # Tokens pro Sekunde berechnen
                    tps = tokens / time_sec if time_sec > 0 else 0

                    # Speichern
                    model_stats[model]['times'].append(time_sec)
                    model_stats[model]['tokens'].append(tokens)
                    model_stats[model]['tps'].append(tps)

                    difficulty_stats[model][difficulty].append(time_sec)
                    row_count += 1

                except ValueError:
                    continue # Überspringe defekte Zeilen

        if row_count == 0:
            print("⚠️ Keine Daten gefunden. Ist die CSV leer?")
            return

        # --- AUSGABE TABELLE 1: GESAMTÜBERSICHT ---
        print("\n🏆 PERFORMANCE ÜBERSICHT (Gesamt)")
        print_separator("=")
        # Header
        print(f"{'Modell':<20} | {'Ø Zeit (s)':<12} | {'Ø Tokens':<10} | {'Ø Speed (T/s)':<15} | {'Anzahl (n)':<10}")
        print_separator()

        for model, data in model_stats.items():
            avg_time = statistics.mean(data['times'])
            avg_tokens = statistics.mean(data['tokens'])
            avg_tps = statistics.mean(data['tps'])
            count = len(data['times'])

            # Median ist oft besser bei Ausreißern
            med_time = statistics.median(data['times'])

            print(f"{model:<20} | {avg_time:<12.2f} | {avg_tokens:<10.1f} | {avg_tps:<15.2f} | {count:<10}")

        print_separator("=")
        print("Hinweis: 'Ø Zeit' ist die Wartezeit des Nutzers. 'T/s' ist die Generierungsgeschwindigkeit.\n")


        # --- AUSGABE TABELLE 2: NACH SCHWIERIGKEIT (DIFFICULTY) ---
        print("\n🧠 ANALYSE NACH SCHWIERIGKEIT (Durchschnittszeit in Sekunden)")
        print_separator("-")

        # Alle Schwierigkeitsgrade finden
        all_diffs = sorted(list({d for m in difficulty_stats for d in difficulty_stats[m]}))

        # Header dynamisch bauen
        header = f"{'Modell':<20}"
        for d in all_diffs:
            header += f" | {d:<12}"
        print(header)
        print_separator()

        for model in model_stats.keys():
            row_str = f"{model:<20}"
            for diff in all_diffs:
                times = difficulty_stats[model].get(diff, [])
                if times:
                    avg = statistics.mean(times)
                    row_str += f" | {avg:<12.2f}"
                else:
                    row_str += f" | {'-':<12}"
            print(row_str)
        print_separator("-")

    except Exception as e:
        print(f"❌ Ein Fehler ist aufgetreten: {e}")

if __name__ == "__main__":
    evaluate_benchmark()