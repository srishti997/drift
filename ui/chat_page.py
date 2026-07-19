import requests
import streamlit as st

from ui.components import recommendation_card, section_header


API_BASE_URL = "http://127.0.0.1:8000"


# ----------------------------------------------------------------------
# API helpers
# ----------------------------------------------------------------------

def get_api(endpoint: str) -> dict:
    try:
        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            timeout=8,
        )
        response.raise_for_status()

        data = response.json()
        return data if isinstance(data, dict) else {}

    except (requests.RequestException, ValueError):
        return {}


def extract_answer(data) -> str:
    if isinstance(data, str):
        return data.strip()

    if not isinstance(data, dict):
        return ""

    for field in (
        "answer",
        "response",
        "message",
        "reply",
        "coach_response",
        "result",
    ):
        value = data.get(field)

        if isinstance(value, str) and value.strip():
            return value.strip()

    advice = data.get("advice")

    if isinstance(advice, list) and advice:
        first_item = advice[0]

        if isinstance(first_item, str):
            return first_item.strip()

        if isinstance(first_item, dict):
            parts = [
                str(first_item.get("observation", "")).strip(),
                str(first_item.get("impact", "")).strip(),
                str(first_item.get("suggestion", "")).strip(),
            ]

            return "\n\n".join(
                part for part in parts if part
            )

    return ""


def build_fallback_answer(
    question: str,
    coach_data: dict,
) -> str:
    question_lower = question.lower()
    advice = coach_data.get("advice", [])

    observation = ""
    impact = ""
    suggestion = ""

    if isinstance(advice, list) and advice:
        first_item = advice[0]

        if isinstance(first_item, dict):
            observation = str(
                first_item.get("observation", "")
            ).strip()

            impact = str(
                first_item.get("impact", "")
            ).strip()

            suggestion = str(
                first_item.get("suggestion", "")
            ).strip()

    if any(
        word in question_lower
        for word in (
            "distract",
            "interruption",
            "lost focus",
            "attention",
        )
    ):
        return (
            observation
            or impact
            or (
                "Your focus was affected by repeated attention changes. "
                "Open Deep Dive to review which context changes became "
                "meaningful distractions."
            )
        )

    if any(
        phrase in question_lower
        for phrase in (
            "what should i do",
            "improve",
            "next",
            "tomorrow",
        )
    ):
        return (
            suggestion
            or (
                "Protect one clear 25–30 minute work block. Close unused "
                "applications, mute notifications, and decide the exact "
                "task before you begin."
            )
        )

    if any(
        phrase in question_lower
        for phrase in (
            "most focused",
            "best focus",
            "deep work",
        )
    ):
        return (
            "Open Deep Dive and review your deep-work sessions and "
            "cognitive timeline. Your strongest period is the longest "
            "uninterrupted productive block."
        )

    parts = [
        part
        for part in (
            observation,
            impact,
            suggestion,
        )
        if part
    ]

    if parts:
        return "\n\n".join(parts)

    return (
        "Drift needs more tracked activity before it can give a specific "
        "answer. Keep the tracker running while you work and ask again."
    )


def ask_coach(question: str) -> str:
    question = str(question or "").strip()

    if not question:
        return "Please enter a question first."

    try:
        response = requests.post(
            f"{API_BASE_URL}/coach",
            json={"question": question},
            timeout=20,
        )

        if response.ok:
            answer = extract_answer(response.json())

            if answer:
                return answer

    except (requests.RequestException, ValueError):
        pass

    try:
        response = requests.get(
            f"{API_BASE_URL}/coach",
            params={"question": question},
            timeout=20,
        )

        if response.ok:
            answer = extract_answer(response.json())

            if answer:
                return answer

    except (requests.RequestException, ValueError):
        pass

    coach_data = get_api("/coach")

    return build_fallback_answer(
        question=question,
        coach_data=coach_data,
    )


# ----------------------------------------------------------------------
# State
# ----------------------------------------------------------------------

def initialise_chat_state() -> None:
    if "coach_messages" not in st.session_state:
        st.session_state.coach_messages = [
            {
                "role": "assistant",
                "content": (
                    "Hi, I’m Drift Coach. Ask me what affected your focus, "
                    "when you worked best, or what you should improve next."
                ),
            }
        ]


def clear_chat() -> None:
    st.session_state.coach_messages = [
        {
            "role": "assistant",
            "content": (
                "Chat cleared. Ask me anything about your workday."
            ),
        }
    ]


# ----------------------------------------------------------------------
# Page
# ----------------------------------------------------------------------

def chat_page():
    initialise_chat_state()

    coach_data = get_api("/coach")
    score_data = get_api("/score")
    report_data = get_api("/daily-report")
    deep_work_data = get_api("/deep-work")

    advice = coach_data.get("advice", [])

    if isinstance(advice, list) and advice:
        primary = advice[0]

        if isinstance(primary, dict):
            observation = primary.get(
                "observation",
                "Your workday has been analysed.",
            )

            impact = primary.get(
                "impact",
                "",
            )

            suggestion = primary.get(
                "suggestion",
                "Protect one uninterrupted focus block next.",
            )
        else:
            observation = str(primary)
            impact = ""
            suggestion = (
                "Protect one uninterrupted focus block next."
            )
    else:
        observation = (
            "Drift needs more activity to understand your work pattern."
        )
        impact = ""
        suggestion = (
            "Keep the tracker running and complete one focused work block."
        )

    overall_score = score_data.get(
        "overall_score",
        0,
    )

    context_switches = report_data.get(
        "context_switches",
        0,
    )

    deep_minutes = deep_work_data.get(
        "total_deep_work_minutes",
        0,
    )

    section_header(
        title="Your productivity coach",
        description=(
            "Ask simple questions about your focus, distractions, "
            "recovery, and what to do next."
        ),
        eyebrow="AI Coach",
    )

    recommendation_card(
        text=str(suggestion),
        label="Coach recommendation",
        icon="💡",
    )

    metric_1, metric_2, metric_3 = st.columns(
        3,
        gap="medium",
    )

    with metric_1:
        with st.container(border=True):
            st.metric(
                "Focus score",
                f"{overall_score}/100",
            )
            st.caption(
                "Your overall focus quality today."
            )

    with metric_2:
        with st.container(border=True):
            st.metric(
                "Attention changes",
                context_switches,
            )
            st.caption(
                "Meaningful context changes detected."
            )

    with metric_3:
        with st.container(border=True):
            st.metric(
                "Deep work",
                f"{deep_minutes} min",
            )
            st.caption(
                "Uninterrupted productive time."
            )

    st.write("")

    left, right = st.columns(
        [1.35, 1],
        gap="large",
    )

    with left:
        with st.container(border=True):
            st.markdown("### 💬 Ask Drift")

            for message in st.session_state.coach_messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            user_question = st.chat_input(
                "Ask what distracted you or what to improve..."
            )

            if user_question:
                st.session_state.coach_messages.append(
                    {
                        "role": "user",
                        "content": user_question,
                    }
                )

                with st.chat_message("user"):
                    st.markdown(user_question)

                with st.chat_message("assistant"):
                    with st.spinner(
                        "Drift is reviewing your workday..."
                    ):
                        response = ask_coach(
                            user_question
                        )

                    st.markdown(response)

                st.session_state.coach_messages.append(
                    {
                        "role": "assistant",
                        "content": response,
                    }
                )

            if st.button(
                "Clear conversation",
                use_container_width=True,
                key="clear_coach_chat",
            ):
                clear_chat()
                st.rerun()

    with right:
        with st.container(border=True):
            st.markdown("### 🧠 What Drift noticed")

            st.markdown(
                f"#### {observation}"
            )

            if impact:
                st.write(impact)

            st.divider()

            st.markdown("### Suggested questions")

            suggested_questions = [
                "What distracted me today?",
                "When was I most focused?",
                "What should I improve tomorrow?",
                "How can I reduce attention changes?",
            ]

            for index, question in enumerate(
                suggested_questions
            ):
                if st.button(
                    question,
                    use_container_width=True,
                    key=f"coach_question_{index}",
                ):
                    st.session_state.coach_messages.append(
                        {
                            "role": "user",
                            "content": question,
                        }
                    )

                    response = ask_coach(question)

                    st.session_state.coach_messages.append(
                        {
                            "role": "assistant",
                            "content": response,
                        }
                    )

                    st.rerun()

        with st.container(border=True):
            st.markdown("### How to use this page")

            st.write(
                "Ask one clear question about your workday."
            )

            st.write(
                "Drift combines your focus score, context changes, "
                "deep-work sessions, and coaching insights."
            )

            st.caption(
                "The quality of the answer improves as more activity "
                "is recorded."
            )