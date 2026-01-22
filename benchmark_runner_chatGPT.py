import json
import csv
import time
import os
from dotenv import load_dotenv
from openai import OpenAI

# 1. API Key laden
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- KONFIGURATION ---
INPUT_FILE = "promptset_test.json"
OUTPUT_FILE = "benchmark_results_chatgpt.csv"
MODEL_NAME = "gpt-5-mini"

# Einstellungen
PARAMS = {
    "temperature": 0.0,
    "seed": 42,
    "top_p": 0.9
}

def build_system_prompt(context_text):
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

def run_benchmark():
    if not os.path.exists(INPUT_FILE):
        print(f"[FEHLER] Datei '{INPUT_FILE}' fehlt.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    fieldnames = [
        "id", "category", "model",
        "time_total", "time_read", "time_write",
        "input_tokens", "output_tokens",
        "tps_read", "tps_write",
        "question", "model_answer", "ground_truth", "context_snippet"
    ]

    file_exists = os.path.exists(OUTPUT_FILE)
    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        if not file_exists:
            writer.writeheader()

        print(f"[INFO] Starte Benchmark mit {MODEL_NAME}...")

        for i, entry in enumerate(questions):
            q_id = entry.get("id")
            print(f"\r[STATUS] Frage {i+1}/{len(questions)} (ID: {q_id})...", end="", flush=True)

            sys_prompt = build_system_prompt(entry.get("context_text", ""))

            try:
                start_time = time.time()

                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": entry.get("question")}
                    ],
                    **PARAMS
                )

                end_time = time.time()

                # Metriken
                duration = end_time - start_time
                usage = response.usage
                in_tok = usage.prompt_tokens
                out_tok = usage.completion_tokens
                content = response.choices[0].message.content
                tps_total = out_tok / duration if duration > 0 else 0

                writer.writerow({
                    "id": q_id,
                    "category": entry.get("category"),
                    "model": MODEL_NAME,
                    "time_total": f"{duration:.3f}",
                    "time_read": "0.000",
                    "time_write": "0.000",
                    "input_tokens": in_tok,
                    "output_tokens": out_tok,
                    "tps_read": "0.00",
                    "tps_write": f"{tps_total:.2f}",
                    "question": entry.get("question"),
                    "model_answer": content,
                    "ground_truth": entry.get("ground_truth"),
                    "context_snippet": entry.get("context_text", "")[:50] + "..."
                })
                csvfile.flush()

            except Exception as e:
                print(f" [FEHLER: {e}] ", end="")

            # PAUSCHALER SLEEP (Sicherheit vor Rate Limits)
            time.sleep(10)

    print(f"\n[INFO] Fertig. Gespeichert in {OUTPUT_FILE}")

if __name__ == "__main__":
    run_benchmark()