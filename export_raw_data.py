import pandas as pd
import os

# --- KONFIGURATION ---
INPUT_FILE = "evaluation_completed.csv"
OUTPUT_FILE = "spaeter loeschen/BA_Rohdaten_Uebersicht_chatgpt.xlsx"

def create_overview_excel():
    if not os.path.exists(INPUT_FILE):
        print(f"[FEHLER] Datei '{INPUT_FILE}' fehlt.")
        return

    print("[STATUS] Verarbeite Daten für Excel-Export...")

    # 1. Daten laden (Semikolon-getrennt)
    try:
        df = pd.read_csv(INPUT_FILE, delimiter=";")
    except Exception as e:
        print(f"[FEHLER] Fehler beim CSV-Lesen: {e}")
        return

    # 2. Datentypen erzwingen (damit Excel damit rechnen kann)
    # Wir fügen hier ALLE neuen Spalten hinzu, die wir im Benchmark-Runner erstellt haben
    numeric_cols = [
        'score',
        'time_total', 'time_read', 'time_write', 'time_sec', # time_sec für Abwärtskompatibilität
        'input_tokens', 'output_tokens',
        'tps_read', 'tps_write'
    ]

    for col in numeric_cols:
        if col in df.columns:
            # errors='coerce' wandelt fehlerhafte Werte in NaN um, statt abzustürzen
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # 3. Excel Writer starten
    try:
        with pd.ExcelWriter(OUTPUT_FILE, engine='openpyxl') as writer:

            # --- BLATT 1: ROHDATEN (Alles) ---
            # Wir sortieren nach ID, damit man Modell A und B direkt untereinander sieht
            if 'id' in df.columns and 'model' in df.columns:
                df_sorted = df.sort_values(by=['id', 'model'])
            else:
                df_sorted = df

            df_sorted.to_excel(writer, sheet_name="Rohdaten_Komplett", index=False)

            # --- BLATT 2: QUALITÄTS-CHECK (Nur Scores) ---
            # Eine Pivot-Tabelle, damit du sofort siehst, ob Daten fehlen
            if 'score' in df.columns:
                pivot_quality = df.pivot_table(
                    index="category",
                    columns="model",
                    values="score",
                    aggfunc=['mean', 'count']
                )
                pivot_quality.to_excel(writer, sheet_name="Check_Scores")

            # --- BLATT 3: EFFIZIENZ (Zeit & Token) ---
            # Hier schauen wir, welche Zeit-Spalte wir haben (time_total ist neu, time_sec alt)
            tech_cols = []
            if 'time_total' in df.columns:
                tech_cols.append('time_total')
            elif 'time_sec' in df.columns:
                tech_cols.append('time_sec')

            if 'tps_write' in df.columns:
                tech_cols.append('tps_write') # Das ist der wichtigste Speed-Wert

            if 'output_tokens' in df.columns:
                tech_cols.append('output_tokens')

            if tech_cols:
                pivot_tech = df.pivot_table(
                    index="model",
                    values=tech_cols,
                    aggfunc=['mean', 'min', 'max']
                )
                pivot_tech.to_excel(writer, sheet_name="Check_Technik")

            # --- BLATT 4: FEHLER-ANALYSE (Nur Scores < 1.0) ---
            if 'score' in df.columns:
                # Filtert alles raus, was perfekt war. Zeigt nur die Fehler.
                df_errors = df[df['score'] < 1.0].copy()

                # Sortieren, falls Spalten existieren
                if 'category' in df_errors.columns:
                    df_errors = df_errors.sort_values(by=['category', 'score'])

                # Wir nehmen nur die wichtigsten Spalten für die Übersicht
                cols_to_keep = ['id', 'category', 'model', 'score', 'question', 'model_answer', 'ground_truth']
                # Prüfen ob alle Spalten da sind
                available_cols = [c for c in cols_to_keep if c in df.columns]

                df_errors[available_cols].to_excel(writer, sheet_name="Nur_Fehler", index=False)

        print(f"[INFO] Datei erstellt: {OUTPUT_FILE}")
        print("       -> Öffne diese Datei jetzt in Excel.")
        print("       -> Blatt 'Rohdaten_Komplett': Hier kannst du filtern.")
        print("       -> Blatt 'Nur_Fehler': Schau dir hier an, WORAN die Modelle gescheitert sind.")

    except Exception as e:
        print(f"[FEHLER] Konnte Excel nicht schreiben: {e}")
        print("[INFO] Stelle sicher, dass die Datei nicht in Excel geöffnet ist!")

if __name__ == "__main__":
    create_overview_excel()