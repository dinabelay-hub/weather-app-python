import cohere, logging

# ⚠️ Hard‑coded key for local use
co = cohere.Client("IN17F4xWlXbuzKJMkjqBymLHd2fcNJAR79uqHaIj")

def get_ai_suggestion(main: str, desc: str, temp: float) -> str | None:
    """
    Return one upbeat activity / advice line via Cohere chat.
    Works with cohere‑python ≥5.x – only `model` and `message`
    plus optional generation params are allowed.
    """
    try:
        user_text = (
            f"Current conditions: {desc} ({main}), {temp}°C.\n"
              "You're SkyCast, a cheerful weather buddy. Suggest ONE fun or feel-good thing to do, "
              "based on the weather — keep it super short and friendly, just one sentence. "
               "Avoid sounding robotic or repeating the same structure and add appropriate emojis."
        )

        resp = co.chat(
            model="command-r-plus",   # free‑tier chat model
            message=user_text,        # USER message
            temperature=0.8,          # optional extras are OK
            max_tokens=50
        )

        return resp.text.strip()
    except Exception as e:
        logging.warning("Cohere suggestion failed: %s", e)
        return None
