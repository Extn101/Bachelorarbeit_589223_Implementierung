# Annahme: Deine Klasse oben heißt "OllamaApi" und ist importiert oder steht hier drüber.
# from ollama_api import OllamaApi  <-- Falls du die Klasse in eine extra Datei gepackt hast

import requests
import json
import re
import ftfy

class OllamaApi:

    HOST = "https://f2ki-h100-1.f2.htw-berlin.de"
    PORT = 11435

    TIMEOUT = 120
    STREAM_RESPONSE = False # Only for debug purposes. !! Result will be null !!

    THINKING = False

    FALSE_RETURN = {"result": None, "time": 0, "token": 0, "info": {}}

    DEFAULT_OPTIONS = {
        "num_ctx": 2048,        # Default: 2048
        "repeat_last_n": 64,    # Default: 64, 0 = disabled, -1 = num_ctx
        "repeat_penalty": 1.1,  # Default: 1.1
        "temperature": 0.8,     # Default: 0.8
        "seed": 0,              # Default: 0
        "stop": [],             # No default
        "num_predict": -1,      # Default: -1, infinite generation
        "top_k": 40,            # Default: 40
        "top_p": 0.9,           # Default: 0.9
        "min_p": 0.0            # Default: 0.0
    }

    @staticmethod
    def fix_invalid_escapes(s):
        if not isinstance(s, str):
            return s

        try:
            s_re = ftfy.fix_text(s)
            if s_re != s:
                s = s_re
        except Exception as e:
            print(f"Encoding failed for text: {e}")

        return s

    @classmethod
    def models(cls):
        url = f"{cls.HOST}:{cls.PORT}/api/tags"
        headers = {
            "accept": "application/json",
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Request failed with status {response.status_code}: {response.text}")
            return False
        else:
            try:
                json_data = response.json()
                return json_data.get("models", [])

            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON: {e}")
                return False

    @classmethod
    def pull_model(cls, name:str, tag:str):
        url = f"{cls.HOST}:{cls.PORT}/api/pull"
        headers = {
            "Content-Type": "application/json",
            "accept": "application/json"
        }
        payload = {
            "model": f"{name}:{tag}"
        }
        try:
            response = requests.post(url, headers=headers, json=payload, stream=True, timeout=cls.TIMEOUT)
            if response.status_code != 200:
                print(f"Pull request failed with status {response.status_code}: {response.text}")
                return False

            for line in response.iter_lines():
                if line:
                    try:
                        progress = json.loads(line)
                        if 'status' in progress:
                            print(f"Pulling model: {progress['status']}")
                        if progress['status'] == "success":
                            return True
                    except json.JSONDecodeError:
                        continue

            return True
        except Exception as e:
            print(f"Failed to pull model: {e}")
            return False

    @classmethod
    def completion(cls, prompt:str, model="phi4:latest", schema=None, options=None):
        payload = {
            "model": model,
            "prompt" : prompt,
            "options": {
                **cls.DEFAULT_OPTIONS,
                **options
            } if options is not None else cls.DEFAULT_OPTIONS,
        }
        if schema is not None:
            payload["format"] = schema

        return cls.api_request(payload, force_json=False if schema is None else True)

    @classmethod
    def chat(cls, chat, model="phi4:latest", schema=None, options=None):
        payload = {
            "model": model,
            "messages": chat,
            "options": {
                **cls.DEFAULT_OPTIONS,
                **options
            } if options is not None else cls.DEFAULT_OPTIONS,
        }
        if schema is not None:
            payload["format"] = schema

        return cls.api_request(payload, force_json=False if schema is None else True)

    @classmethod
    def api_request(cls, payload, force_json:bool):
        if "messages" in payload:
            # Chat Request
            url = f"{cls.HOST}:{cls.PORT}/api/chat"
        else:
            # Completion Request
            url = f"{cls.HOST}:{cls.PORT}/api/generate"

        headers = {
            "Content-Type": "application/json",
            "accept": "application/json"
        }

        payload = {
            **payload,
            "think": cls.THINKING,
            "stream": cls.STREAM_RESPONSE,
            "keep_alive": "5m"
        }

        try:
            response = requests.post(url, headers=headers, json=payload, stream=cls.STREAM_RESPONSE, timeout=cls.TIMEOUT)

            if cls.STREAM_RESPONSE:
                for line in response.iter_lines(decode_unicode=True):
                    try:
                        chunk = json.loads(line)

                        if 'message' in chunk and 'content' in chunk['message']:
                            content = chunk['message']['content']
                            print(content, end='', flush=True)

                        if 'done' in chunk and chunk['done']:
                            break  # Exit the loop if done is True
                    except json.JSONDecodeError as e:
                        print(f"ERROR: Failed to decode JSON during streaming: {e}")
                return {**cls.FALSE_RETURN, "info": {"error": 'Streaming mode does not retreive a value'}}
            else:
                return cls.secure_json_response(response) if force_json else cls.secure_text_response(response)

        except requests.exceptions.Timeout:
            print(f"ERROR: The request took to long. Adjust the timeout ({cls.TIMEOUT}) as needed")
            return {**cls.FALSE_RETURN, "info": {"error": f"Request timeout ({cls.TIMEOUT}) reached"}}
        except Exception as e:
            print(f"ERROR: Request exception: {e}")
            return {**cls.FALSE_RETURN, "info": {"error": f"Request exception: {e}"}}


    @classmethod
    def secure_json_response(cls, response):

        text_response = cls.secure_text_response(response)

        if text_response.get("result") is None:
            return text_response

        message = str(text_response.get("result"))

        markdown_response = False
        thinking_block = False

        if message.strip().startswith("<think>"):
            print('WARN: Model returned <think> reasoning block before JSON')
            message = re.sub(r"^\s*<think>.*?</think>\s*", "", message, flags=re.DOTALL).strip()
            thinking_block = True

        match = re.search(r'```json(.*?)```', message, re.DOTALL)
        if match:
            # Remove everything except the content in "```json" to "```"
            print('WARN: Model returned markdown instead of only JSON')
            message = match.group(1).strip()
            markdown_response = True

        try:
            # Try to parse To json
            result = json.loads(message)

            # Overwrite text result with json dict
            text_response["result"] = dict(result)
            text_response["info"] = {
                "thinking": thinking_block,
                "markdown": markdown_response
            }
            return text_response

        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to decode JSON: {e}")
            return {**cls.FALSE_RETURN, "info": {"error": 'JSON decode error on the model\'s response'}}

        except Exception as e:
            print(f"ERROR: Failed to parse JSON: {e}")
            return {**cls.FALSE_RETURN, "info": {"error": str(e)}}

    @classmethod
    def secure_text_response(cls, response):

        try:
            parsed_json = response.json()

            if response.status_code != 200:
                err_msg = parsed_json.get('error', 'Unknown error')
                print(f"ERROR: Request failed with status {response.status_code}: {err_msg}")
                return {**cls.FALSE_RETURN, "info":{"error":err_msg}}

            if 'done' not in parsed_json or parsed_json.get('done') is False:
                print("ERROR: Response has returned but Model didn't complete the answer")
                return {**cls.FALSE_RETURN, "info": {"error": 'Incomplete answer'}}

            # LLM Chat return as string
            message = parsed_json.get('message').get('content') if "message" in parsed_json else parsed_json.get('response')

            microseconds_elapsed = parsed_json.get('total_duration')
            seconds_elapsed = round(microseconds_elapsed / 1000000000, 3)
            token_count = parsed_json.get('eval_count')

            return {
                "result": cls.fix_invalid_escapes(message),
                "time": float(seconds_elapsed),
                "token": int(token_count),
                "info": {}
            }

        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to decode JSON: {e}")
            return {**cls.FALSE_RETURN, "info": {"error": 'JSON decode error on the ollama server\'s response'}}

        except Exception as e:
            print(f"ERROR: Failed to parse JSON: {e}")
            return {**cls.FALSE_RETURN, "info": {"error": str(e)}}


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