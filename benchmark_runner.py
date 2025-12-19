import json
import csv
import time
import os
from HTW_Ollama_API import OllamaApi  # Deine Datei heißt jetzt so

# --- KONFIGURATION ---
INPUT_FILE = "promptset.json"           # Dein neuer Dateiname
OUTPUT_FILE = "benchmark_results_nfl.csv"

# Deine Modelle
MODELS_TO_TEST = [
    "llama3.1:8b",
    "llama3.3:70b"
]

# Pause zwischen Fragen (kurz, da Modell jetzt im Speicher bleibt)
DELAY_SECONDS = 0.5

# RAG-Einstellungen (Angepasst an H100 Power!)
RAG_OPTIONS = {
    "temperature": 0.1,    # Faktentreue
    "num_ctx": 16384,      # 16k Kontext! Reicht für ca. 40-50 Seiten Text.
    "top_p": 0.9,
}

def run_benchmark():
    # 1. Fragen laden
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Fehler: Datei '{INPUT_FILE}' nicht gefunden.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    # 2. CSV vorbereiten
    file_exists = os.path.exists(OUTPUT_FILE)

    # Mode 'a' (append) ist sicherer, falls das Skript abbricht
    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["id", "category", "difficulty", "model", "time_sec", "tokens", "question", "context_used", "model_answer", "ground_truth", "source"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        print(f"🚀 Starte Benchmark: {len(questions)} Fragen x {len(MODELS_TO_TEST)} Modelle.")
        print(f"💾 Output: {OUTPUT_FILE}")
        print("-" * 60)

        # 3. ÄUßERER LOOP: MODELLE (Optimierung: Modell wird nur 1x geladen)
        for model_name in MODELS_TO_TEST:
            print(f"\n🔵 Lade Modell: {model_name} (Bitte warten...)")

            # Kleiner "Warm-Up" Call, damit das Modell sicher im VRAM liegt
            try:
                OllamaApi.chat([{"role": "user", "content": "Hi"}], model=model_name)
                print("   Modell geladen. Starte Fragen...")
            except Exception as e:
                print(f"   ❌ Fehler beim Laden von {model_name}: {e}")
                continue

            # 4. INNERER LOOP: FRAGEN
            for i, entry in enumerate(questions):
                q_id = entry.get("id")
                question = entry.get("question")
                context = entry.get("context_text", "")

                # Fortschrittsanzeige in einer Zeile (sieht sauberer aus)
                print(f"\r   [{i+1}/{len(questions)}] Frage ID {q_id}...", end="", flush=True)

                # System Prompt bauen
                if context:
                    system_prompt = (
                        "Du bist ein Experte für das NFL-Regelwerk und fungierst als Tutor. "
                        "Deine Aufgabe ist es, Fragen präzise und vollumfassend zu beantworten.\n"
                        "Regeln:\n"
                        "1. Nutze primär den untenstehenden KONTEXT für deine Antwort.\n"
                        "2. Wenn die Info NICHT im Kontext steht, sage: 'Dazu habe ich keine Infos.'\n"
                        "3. Antworte auf Deutsch, nutze aber englische Fachbegriffe.\n"
                        "4. Halte die Antwort so kurz wie möglich, aber so lang wie nötig.\n\n"
                        f"KONTEXT:\n{context}"
                    )
                    context_used = "YES"
                else:
                    system_prompt = "Du bist ein NFL-Regel-Experte. Antworte präzise auf Deutsch mit englischen Fachbegriffen."
                    context_used = "NO"

                chat_messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ]

                try:
                    # API Call
                    response = OllamaApi.chat(chat_messages, model=model_name, options=RAG_OPTIONS)

                    if response and "result" in response:
                        writer.writerow({
                            "id": q_id,
                            "category": entry.get("category", "Unknown"),
                            "difficulty": entry.get("difficulty", "Unknown"),
                            "model": model_name,
                            "time_sec": response["time"],
                            "tokens": response["token"], # Das sind die Output-Tokens
                            "question": question,
                            "context_used": context_used,
                            "model_answer": response["result"],
                            "ground_truth": entry.get("ground_truth", ""),
                            "source": entry.get("source_ref", "")
                        })
                        csvfile.flush() # Sofort speichern
                    else:
                        print(f" (Keine Antwort) ", end="")

                except Exception as e:
                    print(f" (Fehler: {e}) ", end="")

                # Kurze Pause reicht jetzt, da Modell nicht neu geladen werden muss
                time.sleep(DELAY_SECONDS)

            print(f"\n✅ {model_name} abgeschlossen.")

    print("\n🏁 Benchmark komplett fertig!")

if __name__ == "__main__":
    run_benchmark()