import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import csv
import os
import random

# --- KONFIGURATION ---
INPUT_FILE = "benchmark_results_merged.csv"
OUTPUT_FILE = "evaluation_completed.csv"

# Rubrik-Definitionen für die Anzeige
RUBRIC_TEXT = (
    "BEWERTUNGS-LEITFADEN:\n"
    "---------------------------------------------------------\n"
    "🔴 0.0 Pkt (Falsch/Halluzination):\n"
    "   - Antwort widerspricht dem Kontext.\n"
    "   - Erfindet Fakten (Halluzination).\n"
    "   - Bei Kat 4 (Rejection): Modell gibt eine Antwort statt zu verweigern.\n\n"
    "🟡 0.5 Pkt (Teilweise/Ungenau):\n"
    "   - Im Kern richtig, aber wichtige Details fehlen.\n"
    "   - Zu viel irrelevantes Geschwafel (Low Precision).\n\n"
    "🟢 1.0 Pkt (Korrekt & Vollständig):\n"
    "   - Faktisch korrekt laut Kontext.\n"
    "   - Vollständig (alle Bedingungen genannt).\n"
    "   - Bei Kat 4: Korrekte Verweigerung ('Dazu habe ich keine Infos')."
)

class BlindRaterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Blind Evaluation Tool (Bachelor Thesis)")
        # Startgröße erzwingen
        self.root.geometry("1400x900")

        # Daten laden
        self.todo_list = []
        self.current_index = 0
        self.load_data()

        if not self.todo_list:
            messagebox.showinfo("Fertig", "Alle Antworten wurden bereits bewertet!")
            root.destroy()
            return

        # GUI Aufbau
        self.setup_ui()
        self.show_current_question()

        # Tastatur-Shortcuts binden
        self.root.bind('1', lambda event: self.save_rating(0.0))  # Taste 1 -> 0 Punkte
        self.root.bind('2', lambda event: self.save_rating(0.5))  # Taste 2 -> 0.5 Punkte
        self.root.bind('3', lambda event: self.save_rating(1.0))  # Taste 3 -> 1.0 Punkte

    def load_data(self):
        evaluated_ids = set()
        # Prüfen, was schon da ist
        if os.path.exists(OUTPUT_FILE):
            try:
                with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                    # Semikolon wichtig!
                    reader = csv.DictReader(f, delimiter=';')
                    for row in reader:
                        unique_key = f"{row['id']}_{row['model']}"
                        evaluated_ids.add(unique_key)
            except Exception as e:
                print(f"Warnung beim Laden existierender Daten: {e}")

        if not os.path.exists(INPUT_FILE):
            messagebox.showerror("Fehler", f"Datei {INPUT_FILE} nicht gefunden!")
            return

        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter=';')
            rows = list(reader)
            random.shuffle(rows) # Mischen für Blind-Test

            for row in rows:
                unique_key = f"{row['id']}_{row['model']}"
                if unique_key not in evaluated_ids:
                    self.todo_list.append(row)

    def setup_ui(self):
        # Hauptcontainer
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. HEADER (Fortschritt & Kategorie)
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        self.lbl_progress = ttk.Label(header_frame, text="Fortschritt: ...", font=("Arial", 10))
        self.lbl_progress.pack(side=tk.LEFT)

        self.lbl_category = ttk.Label(header_frame, text="Kategorie: ...", font=("Arial", 14, "bold"), foreground="blue")
        self.lbl_category.pack(side=tk.RIGHT)

        # 2. SPLIT SCREEN (Frage/GT vs. Antwort)
        # PanedWindow erlaubt das Verschieben der Trennlinie
        paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        # HIER WAR DER FEHLER: weight=1 entfernt
        paned.pack(fill=tk.BOTH, expand=True)

        # -- Linke Seite: Ground Truth --
        frame_left = ttk.Labelframe(paned, text=" Ground Truth & Kontext ", padding=5)
        paned.add(frame_left, weight=1)

        # Frage Box
        lbl_q = ttk.Label(frame_left, text="Frage:", font=("Arial", 10, "bold"))
        lbl_q.pack(anchor="w")
        self.txt_question = tk.Text(frame_left, height=4, wrap=tk.WORD, font=("Arial", 11), bg="#e6f2ff", padx=5, pady=5)
        self.txt_question.pack(fill=tk.X, pady=(0, 10))

        # GT Box
        lbl_gt = ttk.Label(frame_left, text="Musterlösung (Ground Truth):", font=("Arial", 10, "bold"))
        lbl_gt.pack(anchor="w")
        self.txt_ground_truth = scrolledtext.ScrolledText(frame_left, wrap=tk.WORD, font=("Arial", 11), padx=5, pady=5)
        self.txt_ground_truth.pack(fill=tk.BOTH, expand=True)
        # Tag für Hervorhebung definieren
        self.txt_ground_truth.tag_config("context_mark", foreground="#666666", font=("Arial", 10, "italic"))

        # -- Rechte Seite: Modell Antwort --
        frame_right = ttk.Labelframe(paned, text=" Modell Antwort (Anonym) ", padding=5)
        paned.add(frame_right, weight=1)

        self.txt_model_answer = scrolledtext.ScrolledText(frame_right, wrap=tk.WORD, font=("Arial", 12), bg="#ffffff", padx=10, pady=10)
        self.txt_model_answer.pack(fill=tk.BOTH, expand=True)

        # 3. FOOTER (Rubrik & Buttons) - Fixierte Höhe unten
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill=tk.X, pady=(10, 0), side=tk.BOTTOM)

        # Rubrik Erklärung (Links im Footer)
        lbl_rubric = tk.Label(footer_frame, text=RUBRIC_TEXT, justify=tk.LEFT, bg="#f0f0f0", relief=tk.RIDGE, padx=10, pady=5, font=("Consolas", 9))
        lbl_rubric.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))

        # Buttons (Rechts im Footer)
        btn_frame = ttk.Frame(footer_frame)
        btn_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Button Styles (groß und farbig)
        btn_0 = tk.Button(btn_frame, text="0.0 Punkte\nFalsch / Halluzination\n(Taste: 1)", bg="#ffb3b3", font=("Arial", 11, "bold"),
                          command=lambda: self.save_rating(0.0), height=4)
        btn_0.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        btn_05 = tk.Button(btn_frame, text="0.5 Punkte\nUngenau / Unvollständig\n(Taste: 2)", bg="#ffffb3", font=("Arial", 11, "bold"),
                           command=lambda: self.save_rating(0.5), height=4)
        btn_05.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        btn_1 = tk.Button(btn_frame, text="1.0 Punkte\nKorrekt & Vollständig\n(Taste: 3)", bg="#b3ffb3", font=("Arial", 11, "bold"),
                          command=lambda: self.save_rating(1.0), height=4)
        btn_1.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    def show_current_question(self):
        if self.current_index >= len(self.todo_list):
            messagebox.showinfo("Fertig", "Bewertung abgeschlossen!")
            self.root.destroy()
            return

        data = self.todo_list[self.current_index]

        # Header Infos
        remaining = len(self.todo_list) - self.current_index
        self.lbl_progress.config(text=f"Noch offen: {remaining} | Gesamt in Session: {len(self.todo_list)}")

        # Kategorie einfärben bei Kat 4
        cat_text = data['category']
        if "Out-of-Domain" in cat_text or "Rejection" in cat_text:
            self.lbl_category.config(text=f"⚠️ {cat_text} (ID: {data['id']})", foreground="red")
        else:
            self.lbl_category.config(text=f"{cat_text} (ID: {data['id']})", foreground="blue")

        # 1. Frage
        self.txt_question.config(state=tk.NORMAL)
        self.txt_question.delete(1.0, tk.END)
        self.txt_question.insert(tk.END, data['question'])
        self.txt_question.config(state=tk.DISABLED)

        # 2. Ground Truth + Kontext Snippet
        self.txt_ground_truth.config(state=tk.NORMAL)
        self.txt_ground_truth.delete(1.0, tk.END)
        self.txt_ground_truth.insert(tk.END, data['ground_truth'] + "\n\n")

        # Kontext Snippet anzeigen
        snippet = data.get('context_snippet', '')
        self.txt_ground_truth.insert(tk.END, "--- Verwendeter Kontext-Ausschnitt ---\n", "context_mark")
        self.txt_ground_truth.insert(tk.END, snippet, "context_mark")
        self.txt_ground_truth.config(state=tk.DISABLED)

        # 3. Modell Antwort
        self.txt_model_answer.config(state=tk.NORMAL)
        self.txt_model_answer.delete(1.0, tk.END)
        self.txt_model_answer.insert(tk.END, data['model_answer'])
        self.txt_model_answer.config(state=tk.DISABLED)

    def save_rating(self, score):
        data = self.todo_list[self.current_index]
        data['score'] = score

        file_exists = os.path.exists(OUTPUT_FILE)
        fieldnames = list(data.keys())

        # Speichern
        try:
            with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(data)
        except PermissionError:
            messagebox.showerror("Fehler", f"Bitte schließe die Datei {OUTPUT_FILE} in Excel!")
            return

        self.current_index += 1
        self.show_current_question()

if __name__ == "__main__":
    root = tk.Tk()
    app = BlindRaterApp(root)
    root.mainloop()