import csv
import statistics
import os
from collections import defaultdict

# --- KONFIGURATION ---
INPUT_FILE = "../benchmark_results_open_source.csv"

def print_separator(char="-", length=100):
    print(char * length)

def load_data(filename):
    """
    Liest die CSV-Datei mit dem korrekten Trennzeichen (Semikolon) ein.
    Gibt ein Dictionary mit den gruppierten Daten zurück.
    """
    if not os.path.exists(filename):
        return None

    # Datenstruktur: model -> { 'times': [], 'input_tokens': [], 'output_tokens': [], 'categories': {} }
    stats = defaultdict(lambda: {
        'times': [],
        'input_tokens': [],
        'output_tokens': [],
        'tps': [],
        'categories': defaultdict(list) # Speichert Zeiten pro Kategorie
    })

    try:
        # WICHTIG: delimiter=';' passend zum Benchmark-Skript
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=';')

            for row in reader:
                try:
                    model = row['model']
                    category = row['category']

                    # Zahlen parsen
                    time_sec = float(row['time_sec'])
                    in_tok = int(row['input_tokens'])
                    out_tok = int(row['output_tokens'])

                    # Berechnung Tokens pro Sekunde (TPS)
                    # Nur Output-Tokens zählen für Generierungs-Speed
                    tps = out_tok / time_sec if time_sec > 0 else 0

                    # Daten speichern
                    stats[model]['times'].append(time_sec)
                    stats[model]['input_tokens'].append(in_tok)
                    stats[model]['output_tokens'].append(out_tok)
                    stats[model]['tps'].append(tps)

                    # Für Kategorie-Analyse
                    stats[model]['categories'][category].append(time_sec)

                except ValueError:
                    continue # Kaputte Zeilen überspringen

        return stats

    except Exception as e:
        print(f"Fehler beim Lesen der Datei: {e}")
        return None

def print_performance_table(stats):
    """
    Tabelle 1: Latenz und Geschwindigkeit (Kapitel 6.2.1)
    """
    print("\n1. PERFORMANCE & GESCHWINDIGKEIT (Latenz)")
    print("Interpretation: Wie lange wartet der Nutzer? Wie schnell rechnet der Server?")
    print_separator("=")
    print(f"{'Modell':<20} | {'Ø Zeit (s)':<12} | {'Median (s)':<12} | {'Ø Speed (T/s)':<15} | {'Anzahl (n)':<10}")
    print_separator()

    for model, data in stats.items():
        if not data['times']: continue

        avg_time = statistics.mean(data['times'])
        med_time = statistics.median(data['times'])
        avg_tps = statistics.mean(data['tps'])
        count = len(data['times'])

        print(f"{model:<20} | {avg_time:<12.2f} | {med_time:<12.2f} | {avg_tps:<15.2f} | {count:<10}")
    print_separator("=")

def print_token_cost_table(stats):
    """
    Tabelle 2: Token-Verbrauch (Kapitel 6.1 Kosten)
    """
    print("\n2. TOKEN-ANALYSE (Kosten-Grundlage)")
    print("Interpretation: Input = Kontext-Größe. Output = Wie 'geschwätzig' ist das Modell?")
    print_separator("=")
    print(f"{'Modell':<20} | {'Ø Input (Tok)':<15} | {'Ø Output (Tok)':<15} | {'Ratio (In/Out)':<15}")
    print_separator()

    for model, data in stats.items():
        if not data['times']: continue

        avg_in = statistics.mean(data['input_tokens'])
        avg_out = statistics.mean(data['output_tokens'])

        # Verhältnis: Wie viel Output erzeugt 1 Input? (Nur zur Info)
        ratio = f"1 : {avg_in/avg_out:.1f}" if avg_out > 0 else "-"

        print(f"{model:<20} | {avg_in:<15.1f} | {avg_out:<15.1f} | {ratio:<15}")
    print_separator("=")

def print_category_analysis(stats):
    """
    Tabelle 3: Analyse nach Kategorien (Hypothesen-Prüfung)
    """
    print("\n3. ZEIT-ANALYSE NACH KATEGORIEN (in Sekunden)")
    print("Interpretation: Braucht Reasoning länger als einfaches Retrieval?")
    print_separator("-")

    # Alle vorhandenen Kategorien sammeln
    all_cats = set()
    for m in stats:
        all_cats.update(stats[m]['categories'].keys())
    sorted_cats = sorted(list(all_cats))

    # Header bauen
    header = f"{'Modell':<20}"
    for cat in sorted_cats:
        # Kurze Namen für die Tabelle, falls die Kategorie-Namen sehr lang sind
        short_cat = cat[:15]
        header += f" | {short_cat:<15}"

    print(header)
    print_separator()

    for model, data in stats.items():
        row_str = f"{model:<20}"
        for cat in sorted_cats:
            times = data['categories'].get(cat, [])
            if times:
                avg = statistics.mean(times)
                row_str += f" | {avg:<15.2f}"
            else:
                row_str += f" | {'-':<15}"
        print(row_str)
    print_separator("-")

def main():
    print(f"Lade Daten aus: {INPUT_FILE} ...")
    stats = load_data(INPUT_FILE)

    if not stats:
        print("[FEHLER] Keine Daten gefunden oder Fehler beim Lesen.")
        return

    # Die drei Analysen ausführen
    print_performance_table(stats)
    print_token_cost_table(stats)
    print_category_analysis(stats)

    print("\n[STATUS] Analyse abgeschlossen.")

if __name__ == "__main__":
    main()