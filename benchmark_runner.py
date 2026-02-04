import json
import csv
import time
import os
from HTW_Ollama_API import OllamaApi

# --- KONFIGURATION ---
INPUT_FILE = "promptset.json"
OUTPUT_FILE = "benchmark_results_open_source.csv"

# Modelle
MODELS_TO_TEST = [
    "llama3.1:8b",
    "llama3.3:70b"
]

# Einstellungen (Deterministisch)
CONFIG_OPTIONS = {
    "temperature": 0.0,
    "num_ctx": 8192,
    "seed": 42
}

# --- HILFSFUNKTIONEN ---

def build_system_prompt(context_text):
    """
    Erstellt den System-Prompt.
    Definiert die Rolle, Rejection-Logik und Sprache.
    """
    return (
        "Du bist ein strikter Regel-Analyst für die National Football League (NFL). "
        "Deine Aufgabe ist es, Fragen ausschließlich basierend auf dem untenstehenden Kontext zu beantworten.\n\n"
        "Befolge strikt diese Anweisungen:\n"
        "1. **Wissensbegrenzung:** Nutze NUR Informationen aus dem Abschnitt 'KONTEXT'. Greife NICHT auf dein internes Trainingswissen zurück.\n"
        "2. **Rejection:** Wenn die Antwort auf die Frage nicht eindeutig im Kontext steht, antworte exakt mit: 'Dazu habe ich keine Informationen.' (Erfinde nichts!).\n"
        "3. **Sprache:** Antworte in deutscher Sprache. Behalte englische Fachbegriffe (z.B. 'Touchdown', 'Fumble', 'Line of Scrimmage') bei, da diese im deutschen American Football Standard sind.\n"
        "4. **Präzision:** Antworte direkt und faktenbasiert. Vermeide Einleitungen wie 'Laut dem Text...'.\n\n"
        f"KONTEXT:\n{context_text}"
    )

# --- HAUPTPROGRAMM ---

def run_benchmark():
    # 1. Promptset laden
    if not os.path.exists(INPUT_FILE):
        print(f"[FEHLER] Datei '{INPUT_FILE}' nicht gefunden.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    # 2. CSV vorbereiten
    # Semikolon (;) als Trennzeichen für Excel-Kompatibilität
    file_exists = os.path.exists(OUTPUT_FILE)

    fieldnames = [
        "id",
        "category",
        "model",
        "time_total", "time_read", "time_write", # Detaillierte Zeiten
        "input_tokens", "output_tokens",
        "tps_read", "tps_write",
        "question",
        "model_answer",
        "ground_truth",
        "context_snippet"
    ]

    # Datei im Append-Modus öffnen (falls Skript abbricht, bleiben Daten erhalten)
    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        if not file_exists:
            writer.writeheader()

        print("-" * 60)
        print(f"[INFO] START BENCHMARK")
        print(f"[INFO] Fragen: {len(questions)}")
        print(f"[INFO] Modelle: {MODELS_TO_TEST}")
        print(f"[INFO] Output: {OUTPUT_FILE}")
        print("-" * 60)

        # 3. ÄUßERER LOOP: Durch die Modelle iterieren
        for model_name in MODELS_TO_TEST:
            print(f"\n[INFO] Lade Modell: {model_name}...")

            # Warm-Up Call (Modell in VRAM laden)
            try:
                OllamaApi.chat([{"role": "user", "content": "Hi"}], model=model_name)
                print("   [INFO] Modell bereit.")
            except Exception as e:
                print(f"   [FEHLER] Konnte Modell {model_name} nicht laden: {e}")
                continue

            # 4. INNERER LOOP: Durch die Fragen iterieren
            for i, entry in enumerate(questions):
                q_id = entry.get("id")
                category = entry.get("category")
                question_text = entry.get("question")
                context_text = entry.get("context_text", "")
                ground_truth = entry.get("ground_truth", "")

                # System Prompt bauen
                system_message = build_system_prompt(context_text)

                chat_messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": question_text}
                ]

                print(f"\r   [STATUS] Frage {i+1}/{len(questions)} (ID: {q_id}) an {model_name}...", end="", flush=True)

                try:
                    # --- API AUFRUF ---
                    response = OllamaApi.chat(chat_messages, model=model_name, options=CONFIG_OPTIONS)

                    if response and "result" in response:

                        # --- DATEN VORBEREITEN ---
                        # Werte aus der API holen (mit Fallback auf 0.0)
                        t_total = float(response.get("time", 0))
                        t_read = float(response.get("time_read", 0))
                        t_write = float(response.get("time_write", 0))

                        in_tok = int(response.get("input_token", 0))
                        out_tok = int(response.get("token", 0))

                        # Speed berechnen (Tokens pro Sekunde)
                        # Schutz vor "Division durch Null", falls Zeiten extrem klein sind
                        speed_read = in_tok / t_read if t_read > 0 else 0
                        speed_write = out_tok / t_write if t_write > 0 else 0

                        # --- IN CSV SCHREIBEN ---
                        writer.writerow({
                            "id": q_id,
                            "category": category,
                            "model": model_name,
                            # Zeiten auf 3 Nachkommastellen runden
                            "time_total": f"{t_total:.3f}",
                            "time_read": f"{t_read:.3f}",
                            "time_write": f"{t_write:.3f}",
                            "input_tokens": in_tok,
                            "output_tokens": out_tok,
                            # Speed auf 2 Nachkommastellen runden
                            "tps_read": f"{speed_read:.2f}",
                            "tps_write": f"{speed_write:.2f}",
                            "question": question_text,
                            "model_answer": response["result"],
                            "ground_truth": ground_truth,
                            "context_snippet": context_text[:50] + "..." if context_text else "EMPTY"
                        })
                        csvfile.flush() # Sofort speichern
                    else:
                        print(" [KEINE ANTWORT] ", end="")

                except Exception as e:
                    print(f" [FEHLER: {e}] ", end="")

                # Kurze Pause für Server-Stabilität
                time.sleep(0.2)

            print(f"\n   [INFO] Durchlauf für {model_name} beendet.")

    print("\n[INFO] ALLE TESTS ABGESCHLOSSEN.")
    print(f"[INFO] Ergebnisse gespeichert in: {OUTPUT_FILE}")

if __name__ == "__main__":
    run_benchmark()