# Bachelorarbeit_589223_Implementierung
Ein GitHub-Repo zum speichern und versionieren der Implementierung meiner Bachelorarbeit.
Bachelorarbeit WiSe25/26 Benedict Heidecker.

## Implementierungen und Inhalt
Es wurden Pythonbackends zum Abrufen der Chatfunktionalität der Modelle Llama 3.1 8B und 3.3 70B, ChatGPT 5 Mini und Gemini 3 Flash erstellt.
Diese Backends führen Benchmarks durch, indem sie Fragen aus einem Promptset an die Modelle senden und die Antworten sowie verschiedene Metriken aufzeichnen.
Das Promptset enthält Fragen aus den vier verschiedenen Kategorien "Information Retrieval", "Reasoning & Synthesis", "Regulatory Constraints" und "Out-of-Domain".
Das Promptset wurde selbst erstellt und enthält Kontext, um den Ansatz des "Context-Augumented Generation" zu verfolgen. 
Der Kontext basiert auf dem offiziellen Regelwerk der National Football League (vgl. Goodell, 2025).
Das Ziel der Benchmarks ist es, die Leistung der Modelle in Bezug auf Antwortgenauigkeit, Antwortzeit und Token-Verbrauch zu vergleichen.
Die Analyse der Ergebnisse erfolgt außerhalb dieses Repositories.

## Verzeichnisstruktur
Dateien zum Abrufen der Modelle:

benchmark_runner.py - für die Llama 3 Modelle

benchmark_runner_gpt.py - für das Modell ChatGPT 5 Mini

benchmark_runner_gemini.py - für das Modell Gemini 3 Flash

Diese Dateien enthalten den Code, um die jeweiligen Modelle zu laden und die Benchmarks durchzuführen, sowie die Ergebnisse zu speichern.

### Ergebnisdateien
Die Ergebnisse der Benchmarks werden in CSV-Dateien gespeichert:

benchmark_results_open_source.csv - Ergebnisse der beiden Open-Source-Modelle

benchmark_results_chatgpt(_ohne_duplikate).csv - Ergebnisse des ChatGPT 5 Mini Modells

benchmark_results_gemini(2-4).csv - Ergebnisse des Gemini 3 Flash Modells

Diese Dateien enthalten die unbewerteten Daten der Benchmarks.
Enthalten sind: id;category;model;time_total;time_read;time_write;input_tokens;output_tokens;tps_read;tps_write;question;model_answer;ground_truth;context_snippet

Die Daten wurden nach einem Durchlauf mit der Hilfsdatei check_data.py überprüft.
Bei Einträgen die Fehlerhaft waren, weil keine Metadaten mitgeschickt oder weil ein ERROR 503 aufgetreten ist, wurden die entsprechenden Fragen erneut abgerufen.

Die Daten wurden dann mit der Hilfsdatei merge_csv.py zusammengeführt:

benchmark_results_merged.csv - zusammengeführte Ergebnisse aller Modelle

### Bewertete Ergebnisdatei
Die bewerteten Ergebnisse der Benchmarks werden in csv-Datei gespeichert:

evaluation_completed.csv - bewertete Ergebnisse aller Modelle

Um die Ergebnisse blind zu bewerten, wurde die Hilfsdatei rate_answers.py verwendet. 
Sie erstellt eine kleine GUI, mit der die Antworten der Modelle, ohne Modellname, dargestellt und über Buttons mit 1, 0,5 oder 0 bewertet werden konnten.

Die bewerteten Ergebnisse wurden mit der Hilfsdatei export_raw_data.py in eine xlsx-Datei exportiert, um die Analyse in Excel durchzuführen.
BA_Rohdaten_Uebersicht.xlsx - Rohdaten der bewerteten Ergebnisse

Die Analyse der Endergebnisse wurde von mir per Hand vorgenommen.

### API der HTW Berlin
Die Datei HTW_Ollama_API.py enthält eine Klasse zur Interaktion mit der HTW Berlin Ollama-API.
Der Inhalt dieser Datei wurde von Sönke Tenckhoff (vgl., 2025) online für den Zugriff auf die Modelle zur Verfügung gestellt und ermöglicht das Senden von Anfragen an die API und das Empfangen von Antworten der Modelle.

Diese Schnittstelle wurde in den Benchmark Runner Dateien verwendet, um die Modelle zu testen, und wurde leicht in der Methode "def secure_text_response(cls, response):" angepasst. Siehe Kommentar in der Datei.

### Promptset
Die Datei promptset.json enthält die Fragen und Antworten, die für die Benchmarks verwendet wurden.

Die Struktur der JSON-Datei ist wie folgt:
"id":
"category":
"question":
"ground_truth":
"source_ref":
"context_text":

###  Einsatz von KI-Tools
Bei der Implementierung des Codes wurde das KI-Tool Gemini für Folgendes eingesetzt:
Unterstützung bei dem Erstellen durch Generieren des Python-Codes sowie Unterstützung bei der Generierung der json-Struktur, sowie Ideengenerierung für die Fragen der Fragenkategorie "Out-of-Domain".

## Quellen
Goodell, R. (2025). OFFICIAL PLAYING RULES OF THE NATIONAL FOOTBALL LEAGUE. National Football League. https://operations.nfl.com/the-rules/nfl-rulebook/

Tenckhoff, S. (2025). Htw-ollama-py/emxamples.py. GitHub. https://github.com/sotenck/htw-ollama-py/blob/main/examples.py

## Lizenzhinweise

Dieses Repository verwendet ein duales Lizenzmodell für Software und Daten, unter Berücksichtigung von Rechten Dritter.

### 1. Software (Quellcode)
Der in diesem Repository enthaltene Quellcode (z. B. `.py` Dateien), soweit er von mir selbst erstellt wurde, ist unter der **MIT Lizenz** veröffentlicht.
Dies gestattet die Nutzung, Veränderung und Verbreitung unter der Bedingung der Namensnennung.

> Copyright (c) 2026 [Benedict Heidecker]

**Ausnahmen im Quellcode:**
* Die Datei `HTW_Ollama_API.py` basiert auf der Arbeit von Sönke Tenckhoff (2025) und unterliegt dessen ursprünglichen Urheberrechtsbestimmungen bzw. Lizenzvorgaben.

### 2. Daten (Promptset & Ergebnisse)
Die erstellten Datensätze (insbesondere `benchmark_results_*.csv`, `evaluation_completed.csv` und die Struktur sowie die Fragen in `promptset.json`) sind lizenziert unter der **Creative Commons Attribution 4.0 International (CC BY 4.0)(http://creativecommons.org/licenses/by/4.0/)** Lizenz.

**Wichtiger rechtlicher Hinweis zu Fremdinhalten:**
* Die Datei `promptset.json` enthält Textauszüge aus dem offiziellen Regelwerk der National Football League (NFL).
* Diese Inhalte (`context_text`) sind **nicht** Teil der CC BY 4.0 Lizenzierung dieses Repositories. Das Urheberrecht für diese Texte liegt allein bei der National Football League (NFL). Die Nutzung in diesem Projekt erfolgt zu wissenschaftlichen Analysezwecken.

### 3. KI-Generierte Inhalte
Teile des Codes und der Datenstruktur wurden unter Assistenz von generativer KI (Google Gemini) erstellt. Gemäß der aktuellen Rechtsauffassung mache ich für rein KI-generierte Fragmente keine gesonderten Urheberrechte geltend, übernehme jedoch die Verantwortung für die Integration in dieses Projekt.

## Datenverfügbarkeit und Löschkonzept
Im Sinne der "Guten wissenschaftlichen Praxis" und zur Gewährleistung der dauerhaften Reproduzierbarkeit der Ergebnisse ist **keine Löschung** dieses Repositories vorgesehen.
* **Status:** Das Repository wird nach Abschluss des Bewertungsverfahrens in den Status "Public Archive" (Read-Only) versetzt.
* **Löschdatum:** Entfällt (Long-term Archiving).