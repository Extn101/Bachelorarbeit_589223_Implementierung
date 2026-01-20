import json
import csv
import time
import os
import tiktoken
from HTW_Ollama_API import OllamaApi

# --- KONFIGURATION ---
INPUT_FILE = "promptset_TEST.json"
OUTPUT_FILE = "benchmark_results_nfl.csv"

# Modelle
MODELS_TO_TEST = [
    "llama3.1:8b",
    "llama3.3:70b"
]

# Einstellungen (Deterministisch)
RAG_OPTIONS = {
    "temperature": 0.0,
    "num_ctx": 16384,
    "top_p": 0.9,
    "seed": 42
}

# --- HILFSFUNKTIONEN ---

def count_tokens(text):
    """
    Zaehlt die Tokens fuer die Kostenberechnung.
    """
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
        return len(encoding.encode(text))
    except Exception as e:
        print(f"[FEHLER] Token-Zaehlung fehlgeschlagen: {e}")
        return 0

def build_system_prompt(context_text):
    """
    Erstellt den System-Prompt.
    Geht davon aus, dass IMMER Kontext vorhanden ist (auch bei Kat 4).
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
    # 1. Datei laden
    if not os.path.exists(INPUT_FILE):
        print(f"[FEHLER] Datei '{INPUT_FILE}' nicht gefunden.")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    # 2. CSV vorbereiten
    # WICHTIG: Wir nutzen jetzt das Semikolon als Trennzeichen fuer bessere Kompatibilitaet
    file_exists = os.path.exists(OUTPUT_FILE)

    fieldnames = [
        "id",
        "category",
        "model",
        "time_sec",
        "input_tokens",
        "output_tokens",
        "question",
        "model_answer",
        "ground_truth",
        "context_snippet"
    ]

    # delimiter=';' sorgt dafuer, dass Excel die Spalten in Deutschland direkt erkennt
    # quotechar='"' sorgt dafuer, dass Text in Anfuehrungszeichen gesetzt wird, falls er ein Semikolon enthaelt
    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        if not file_exists:
            writer.writeheader()

        print("-" * 60)
        print(f"[INFO] START BENCHMARK")
        print(f"[INFO] Fragen: {len(questions)}")
        print(f"[INFO] Modelle: {MODELS_TO_TEST}")
        print("-" * 60)

        # 3. Schleife ueber Modelle
        for model_name in MODELS_TO_TEST:
            print(f"\n[INFO] Lade Modell: {model_name}...")

            # Warm-Up
            try:
                OllamaApi.chat([{"role": "user", "content": "Hallo"}], model=model_name)
                print("   [INFO] Modell bereit.")
            except Exception as e:
                print(f"   [FEHLER] Konnte Modell {model_name} nicht laden: {e}")
                continue

            # 4. Schleife ueber Fragen
            for i, entry in enumerate(questions):
                q_id = entry.get("id")
                category = entry.get("category")
                question_text = entry.get("question")
                context_text = entry.get("context_text", "") # Ist jetzt nie leer (durch Distraktoren)
                ground_truth = entry.get("ground_truth", "")

                # System Prompt & Token
                system_message = build_system_prompt(context_text)
                total_input_text = system_message + "\n" + question_text
                input_token_count = count_tokens(total_input_text)

                chat_messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": question_text}
                ]

                print(f"\r   [STATUS] Frage {i+1}/{len(questions)} (ID: {q_id}) an {model_name}...", end="", flush=True)

                try:
                    response = OllamaApi.chat(chat_messages, model=model_name, options=RAG_OPTIONS)

                    if response and "result" in response:
                        writer.writerow({
                            "id": q_id,
                            "category": category,
                            "model": model_name,
                            "time_sec": response["time"],
                            "input_tokens": input_token_count,
                            "output_tokens": response["token"],
                            "question": question_text,
                            "model_answer": response["result"],
                            "ground_truth": ground_truth,
                            "context_snippet": context_text[:50] + "..." if context_text else "EMPTY"
                        })
                        csvfile.flush()
                    else:
                        print(" [KEINE ANTWORT] ", end="")

                except Exception as e:
                    print(f" [FEHLER: {e}] ", end="")

                time.sleep(0.2)

            print(f"\n   [INFO] Durchlauf fuer {model_name} beendet.")

    print("\n[INFO] ALLE TESTS ABGESCHLOSSEN.")
    print(f"[INFO] Ergebnisse gespeichert in: {OUTPUT_FILE}")

if __name__ == "__main__":
    run_benchmark()