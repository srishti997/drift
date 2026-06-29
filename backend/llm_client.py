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
print("API KEY:", os.getenv("GEMINI_API_KEY"))


def generate_ai_response(prompt: str):
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return {
            "answer": "Gemini API key is missing. Add GEMINI_API_KEY to your .env file.",
            "provider": "gemini",
            "success": False,
        }

    try:
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        response = model.generate_content(prompt)

        return {
            "answer": response.text,
            "provider": "gemini",
            "success": True,
        }

    except Exception as error:
        return {
            "answer": f"Gemini failed: {str(error)}",
            "provider": "gemini",
            "success": False,
        }