import requests

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
API_KEY = "PASTE_YOUR_HUGGINGFACE_API_KEY"

# Good free chat model (stable)
MODEL = "HuggingFaceH4/zephyr-7b-beta"

API_URL = f"https://api-inference.huggingface.co/models/{MODEL}"

headers = {
    "Authorization": f"Bearer {API_KEY}"
}

# ──────────────────────────────────────────────
def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
    return response.json()

# ──────────────────────────────────────────────
def chat():
    print("===================================")
    print("   HUGGING FACE CHATBOT 🤗")
    print("   type 'exit' to quit")
    print("===================================\n")

    history = ""

    while True:
        user_input = input("YOU: ").strip()

        if user_input.lower() in ["exit", "quit"]:
            print("👋 done testing")
            break

        if not user_input:
            continue

        # Build prompt (important for chat style)
        history += f"\nUser: {user_input}\nAssistant:"

        print("AI: ...thinking...\n")

        try:
            output = query({
                "inputs": history,
                "parameters": {
                    "max_new_tokens": 200,
                    "temperature": 0.7
                }
            })

            if isinstance(output, dict) and "error" in output:
                print("❌ API Error:", output["error"])
                continue

            reply = output[0]["generated_text"].split("Assistant:")[-1].strip()

            print("AI:", reply, "\n")

            history += " " + reply

        except Exception as e:
            print("❌ Error:", e)


# ──────────────────────────────────────────────
if __name__ == "__main__":
    chat()
