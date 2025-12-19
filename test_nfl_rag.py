from HTW_Ollama_API import OllamaApi


if __name__ == "__main__":

    # 1. WÄHLE DAS MODELL
    # Wir starten mit dem kleinen, um zu sehen ob es läuft.
    # Später änderst du das auf "llama3.3:70b"
    MODEL_TO_TEST = "llama3.3:70b"

    print(f"🚀 Starte RAG-Simulation mit Modell: {MODEL_TO_TEST}...\n")

    # 2. DER KONTEXT (Simuliert das, was deine Vektordatenbank später liefert)
    # Auszug aus NFL Rule 12 (Player Conduct)
    nfl_context_chunk = """
    SECTION 2 - PERSONAL FOULS
    ARTICLE 6. UNNECESSARY ROUGHNESS. There shall be no unnecessary roughness. This shall include, but will not be limited to:
    (a) using the foot or any part of the leg to strike an opponent with a whipping motion (leg whip);
    (b) contacting a runner when he is on the ground and no longer attempting to advance;
    (c) running, diving into, or throwing the body against or on a player who (1) is out of the play or (2) should not have reasonably anticipated such contact by an opponent, before or after the ball is dead;
    (d) contacting a runner who is in a defenseless posture (by throwing the ball) with the crown of the helmet.
    
    Penalty: For unnecessary roughness: Loss of 15 yards. The player may be disqualified if the action is judged by the official(s) to be flagrant.
    """

    # 3. DIE FRAGE DES STUDENTS
    user_question = "Was passiert, wenn ich einen Spieler tackle, der schon am Boden liegt und nichts mehr macht?"

    # 4. DER SYSTEM-PROMPT (Die Anweisung an den KI-Tutor)
    system_prompt = f"""
    Du bist ein hilfreicher KI-Tutor für NFL-Regeln.
    Beantworte die Frage des Nutzers NUR basierend auf dem untenstehenden Kontext.
    Wenn die Antwort nicht im Kontext steht, sage "Das weiß ich nicht basierend auf diesem Text".
    Halte die Antwort kurz und präzise auf Deutsch.
    
    KONTEXT:
    {nfl_context_chunk}
    """

    # 5. CHAT AUFBAUEN
    chat_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_question}
    ]

    # 6. EINSTELLUNGEN (WICHTIG!)
    my_options = {
        "temperature": 0.1,    # WICHTIG: Niedrig für Fakten!
        "num_ctx": 4096,       # Genug Platz für den Kontext
    }

    # 7. AUSFÜHREN
    result = OllamaApi.chat(chat_messages, model=MODEL_TO_TEST, options=my_options)

    # 8. ERGEBNIS ANZEIGEN
    if result and "result" in result:
        print("-" * 30)
        print(f"🤖 Antwort von {MODEL_TO_TEST}:")
        print("-" * 30)
        print(result["result"])
        print("-" * 30)
        print(f"⏱️  Dauer: {result['time']}s | Tokens: {result['token']}")
    else:
        print("❌ Fehler beim Abruf.")