import pandas as pd
import os

# --- KONFIGURATION ---
# Trage hier exakt die Dateinamen ein, die du zusammenfügen willst
FILES_TO_MERGE = [
    "benchmark_results_chatgpt_ohne_duplikat.csv",
    "benchmark_results_gemini.csv",
    "benchmark_results_gemini_erweiterung.csv",
    "benchmark_results_gemini_erweiterung2.csv",
    "benchmark_results_gemini_erweiterung3.csv",
    "benchmark_results_gemini_erweiterung4.csv",
    "benchmark_results_open_source.csv"
    ]

OUTPUT_FILE = "benchmark_results_merged.csv"

def merge_simple():
    all_dfs = []
    print("[STATUS] Starte Merge-Vorgang...")

    for filename in FILES_TO_MERGE:
        if not os.path.exists(filename):
            print(f"[WARNUNG] Datei nicht gefunden (wird uebersprungen): {filename}")
            continue

        try:
            # CSV lesen (Semikolon-getrennt)
            df = pd.read_csv(filename, delimiter=";")
            original_count = len(df)

            # --- FILTERUNG ---
            # Wir entfernen Zeilen, wo 'model_answer' das Wort 'ERROR' enthaelt
            # Wir wandeln erst in String um, falls da komische Werte drin sind
            # case=False bedeutet: egal ob 'ERROR', 'Error' oder 'error'
            df_clean = df[~df["model_answer"].astype(str).str.contains("ERROR", case=False, na=False)]

            # Zusaetzlich filtern wir explizit 'UNAVAILABLE' (Google 503 Fehler)
            df_clean = df_clean[~df_clean["model_answer"].astype(str).str.contains("UNAVAILABLE", case=False, na=False)]

            filtered_count = len(df_clean)
            removed = original_count - filtered_count

            all_dfs.append(df_clean)
            print(f"[INFO] Datei '{filename}' geladen. {removed} Fehler-Zeilen entfernt. {filtered_count} Zeilen behalten.")

        except Exception as e:
            print(f"[FEHLER] Konnte Datei '{filename}' nicht lesen: {e}")

    if not all_dfs:
        print("[FEHLER] Keine Daten geladen. Abbruch.")
        return

    # Alles zusammenfuegen
    full_df = pd.concat(all_dfs, ignore_index=True)

    # Sortieren nach ID (damit du das Duplikat leichter findest)
    if 'id' in full_df.columns:
        full_df['id'] = pd.to_numeric(full_df['id'], errors='coerce')
        full_df = full_df.sort_values(by=['id', 'model'])

    # Speichern (wieder als Semikolon-CSV fuer Excel)
    full_df.to_csv(OUTPUT_FILE, sep=";", index=False, encoding="utf-8")

    print(f"[STATUS] Fertig.")
    print(f"[INFO] Gesamtzeilen: {len(full_df)}")
    print(f"[INFO] Datei gespeichert unter: {OUTPUT_FILE}")

if __name__ == "__main__":
    merge_simple()