import os
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

print("Looking for:", ENV_FILE)
print("Env exists:", ENV_FILE.exists())

loaded = load_dotenv(dotenv_path=ENV_FILE)

print("Dotenv loaded:", loaded)
print("API key loaded:", bool(os.getenv("GEMINI_API_KEY")))
loaded = load_dotenv(dotenv_path=ENV_FILE)
DEMO_MODE = (
    os.getenv("DRIFT_DEMO_MODE", "false")
    .lower()
    == "true"
)

def generate_ai_response(prompt: str):
    api_key = os.getenv("GEMINI_API_KEY")

    if DEMO_MODE:
        return {
            "answer": (
            "Drift is running in Demo Mode.\n\n"
            "The activity was analysed successfully, "
            "but external AI generation has been disabled.\n\n"
            "Disable DRIFT_DEMO_MODE in your .env file to use Gemini."
        ),
        "provider": "drift-demo",
        "success": True,
    }

    if not api_key:
        return {
            "answer": "Gemini API key is missing.",
            "provider": "gemini",
            "success": False,
        }

    try:
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel("gemini-2.0-flash")

        response = model.generate_content(prompt)

        return {
            "answer": response.text,
            "provider": "gemini",
            "success": True,
        }

    except Exception as error:
        error_message = str(error)

        if "429" in error_message or "quota" in error_message.lower():
            return {
                "answer": "The AI reasoning service is temporarily unavailable due to API quota limits. Please try again in a few minutes.",
                "provider": "gemini",
                "success": False,
            }

        return {
            "answer": f"Gemini Error: {error_message}",
            "provider": "gemini",
            "success": False,
        }