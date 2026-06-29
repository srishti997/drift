from backend.context_builder import build_behavior_context
from backend.prompt_builder import build_drift_prompt
from backend.llm_client import generate_ai_response


def answer_user_question(question: str, activity_logs):
    context = build_behavior_context(activity_logs)
    prompt = build_drift_prompt(question, context)

    ai_response = generate_ai_response(prompt)

    return {
        "answer": ai_response["answer"],
        "provider": ai_response["provider"],
        "success": ai_response["success"],
        "confidence": 0.9 if ai_response["success"] else 0.3
    }