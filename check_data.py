import pandas as pd
import os

# --- HIER DEINE DATEIEN EINTRAGEN ---
FILES_TO_CHECK = [
    "benchmark_results_gemini.csv",
    "benchmark_results_chatgpt.csv",
    "benchmark_results_open_source.csv",
    "benchmark_results_gemini_erweiterung.csv",
    "benchmark_results_gemini_erweiterung2.csv",
    "benchmark_results_gemini_erweiterung3.csv",
]

def check_csv(filename):
    print(f"\n PRÜFE: {filename} ...")

    if not os.path.exists(filename):
        print(f" Datei nicht gefunden!")
        return

    try:
        # Semikolon als Trenner beachten!
        df = pd.read_csv(filename, delimiter=";")
    except Exception as e:
        print(f" Kritisches Format-Problem (kann CSV nicht lesen): {e}")
        return

    # 1. Zeilen zählen
    row_count = len(df)
    print(f"   -> Anzahl Antworten: {row_count}")

    # 2. Auf Duplikate prüfen (IDs)
    if "id" in df.columns:
        duplicates = df[df.duplicated("id")]
        if not duplicates.empty:
            print(f"    ACHTUNG: {len(duplicates)} doppelte IDs gefunden!")


    # 3. Nach Fehlermeldungen im Text suchen
    error_keywords = ["ERROR", "Exception", "Traceback", "EMPTY RESPONSE", "BLOCKED"]
    error_rows = df[df["model_answer"].str.contains("|".join(error_keywords), case=False, na=False)]

    if not error_rows.empty:
        print(f"    {len(error_rows)} Zeilen enthalten FEHLER-Texte:")
        for idx, row in error_rows.iterrows():
            print(f"      - ID {row.get('id', '?')}: {row.get('model_answer', '')[:50]}...")
    else:
        print("    Keine offensichtlichen Fehlermeldungen in den Antworten.")

    # 4. Leere Antworten prüfen
    empty_answers = df[df["model_answer"].isna() | (df["model_answer"].astype(str).str.strip() == "")]
    if not empty_answers.empty:
        print(f"    {len(empty_answers)} Antworten sind komplett LEER.")

    # 5. Token-Plausibilität
    if "output_tokens" in df.columns:
        zero_tokens = df[df["output_tokens"] == 0]
        if not zero_tokens.empty:
            print(f"    {len(zero_tokens)} Zeilen haben 0 Output Tokens (technisch verdächtig).")

if __name__ == "__main__":
    for f in FILES_TO_CHECK:
        check_csv(f)