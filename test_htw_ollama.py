from HTW_Ollama_API import OllamaApi

if __name__ == "__main__":

    # Load all available models by name
    models = OllamaApi.models()
    model_names = [model.get("name") for model in models]
    print(f"\n-------\nAvailable models ({len(model_names)}):")
    print(" | ".join(model_names))

    # Download a specific model
    # OllamaApi.pull_model("llama4","17b-scout-16e-instruct-q8_0")

    # Define Model to use for examples
    model_name = "gemma3:12b"
    print(f"-------\nUsing model {model_name}:")

    # Example 1
    # Prompt Completion - Text return
    print("\n------\nExample 1:")

    msg = "Please write me your favourite haiku"
    completion_result = OllamaApi.completion(msg, model=model_name)
    print(json.dumps(completion_result, indent=4))
    print(f"\nResult:\n{completion_result.get('result')}")

    # Example 2
    # Chat - Text return
    print("\n------\nExample 2:")

    chat_context = [
        {"role": "system", "content": "You are a HAIKU master"},
        {"role": "user", "content": msg}
        # ... more entries if wanted
    ]
    chat_result = OllamaApi.chat(chat_context, model=model_name)
    print(json.dumps(chat_result, indent=4))
    print(f"\nResult:\n{chat_result.get('result')}")

    # Example 3
    # Prompt Completion - Json return
    print("\n------\nExample 3:")

    schema = {
        "type": "object",
        "description": "Defines the required structure for all lines of a Haiku",
        "properties": {
            "lines": {
                "type": "array",
                "description": "A list of lines that make up the Haiku",
                "items": {
                    "type": "string",
                    "description": "A single line of the Haiku"
                }
            }
        },
        "required": ["lines"]
    }
    completion_json_result = OllamaApi.completion(msg, model=model_name, schema=schema)
    print(json.dumps(completion_json_result, indent=4, ensure_ascii=False))
    print(f"\nResult:\n{json.dumps(completion_json_result.get('result'), indent=4, ensure_ascii=False)}")


    # Example 4
    # Chat - Json return
    print("\n------\nExample 4:")

    # we re-use the chat context from example 2 as well as the json schema from example 3
    chat_json_result = OllamaApi.chat(chat_context, model=model_name, schema=schema)
    print(json.dumps(chat_json_result, indent=4, ensure_ascii=False))
    print(f"\nResult:\n{json.dumps(chat_json_result.get('result'), indent=4, ensure_ascii=False)}")