import json
import csv
import time
import os
from dotenv import load_dotenv

from google import genai
from google.genai import types

# 1. API Key laden
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    print("[FEHLER] Kein GOOGLE_API_KEY in der .env gefunden!")
    exit()

client = genai.Client(api_key=API_KEY)

# --- KONFIGURATION ---
INPUT_FILE = "promptset.json"
OUTPUT_FILE = "benchmark_results_gemini_erweiterung4.csv"
MODEL_NAME = "gemini-3-flash-preview"

generate_config = types.GenerateContentConfig(
    temperature=0.0,
    top_p=0.9
)

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

        print(f"[INFO] Starte Benchmark (FAST MODE) mit {MODEL_NAME}...")

        for i, entry in enumerate(questions):
            q_id = entry.get("id")
            print(f"\r[STATUS] Frage {i+1}/{len(questions)} (ID: {q_id})...", end="", flush=True)

            sys_prompt = build_system_prompt(entry.get("context_text", ""))
            full_prompt = sys_prompt + "\n\nFRAGE:\n" + entry.get("question")

            try:
                start_time = time.time()

                # API Aufruf (Kein Retry, kein Loop)
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=full_prompt,
                    config=generate_config
                )

                end_time = time.time()
                duration = end_time - start_time

                # Text-Extraktion (Minimale Fehlerbehandlung)
                content = ""
                if response.text:
                    content = response.text
                elif response.candidates and response.candidates[0].content.parts:
                    content = response.candidates[0].content.parts[0].text
                else:
                    content = "[EMPTY RESPONSE]"

                # Tokens
                in_tok = 0
                out_tok = 0
                if response.usage_metadata:
                    in_tok = response.usage_metadata.prompt_token_count
                    out_tok = response.usage_metadata.candidates_token_count

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
                # Bei Fehler sofort weitermachen, aber Fehler loggen
                print(f" [FEHLER: {e}] ", end="")
                writer.writerow({
                    "id": q_id,
                    "category": entry.get("category"),
                    "model": MODEL_NAME,
                    "time_total": "0.000",
                    "time_read": "0.000", "time_write": "0.000",
                    "input_tokens": 0, "output_tokens": 0,
                    "tps_read": "0.00", "tps_write": "0.00",
                    "question": entry.get("question"),
                    "model_answer": f"ERROR: {str(e)}",
                    "ground_truth": entry.get("ground_truth"),
                    "context_snippet": "ERROR"
                })
                csvfile.flush()

    print(f"\n[INFO] Fertig. Gespeichert in {OUTPUT_FILE}")

if __name__ == "__main__":
    run_benchmark()