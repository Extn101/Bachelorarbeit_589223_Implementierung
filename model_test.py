from HTW_Ollama_API import OllamaApi


if __name__ == "__main__":

    # Load all available models by name
    models = OllamaApi.models()
    model_names = [model.get("name") for model in models]
    print(f"\n-------\nAvailable models ({len(model_names)}):")
    print(" | ".join(model_names))