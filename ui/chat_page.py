import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"


def ask_ai(question: str):
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={
                "question": question
            },
            timeout=120,
        )

        if response.status_code == 200:
            return response.json()

    except Exception as e:
        return {
            "answer": f"Connection error: {e}",
            "provider": "drift",
            "success": False,
            "confidence": 0,
        }

    return {
        "answer": "Unable to reach AI.",
        "provider": "drift",
        "success": False,
        "confidence": 0,
    }


def chat_page():

    st.markdown("""
    <div style="
        margin-bottom:25px;
    ">
        <div style="
            color:#22D3EE;
            font-size:11px;
            font-weight:800;
            letter-spacing:.18em;
            text-transform:uppercase;
        ">
            AI COACH
        </div>

        <h1 style="
            color:white;
            margin-top:8px;
        ">
            Ask Drift anything.
        </h1>

        <p style="
            color:#94A3B8;
            font-size:15px;
        ">
            Natural language coaching powered by your activity history.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    suggestions = [
        "Why was my productivity low today?",
        "What distracted me most?",
        "How can I improve tomorrow?",
        "What mission consumed most of my time?",
        "Did I recover well after distractions?"
    ]

    st.markdown("#### Suggested Questions")

    cols = st.columns(len(suggestions))

    for col, q in zip(cols, suggestions):
        with col:
            if st.button(q):
                st.session_state.pending_question = q

    st.divider()

    for msg in st.session_state.messages:

        with st.chat_message(msg["role"]):

            st.markdown(msg["content"])

            if msg["role"] == "assistant":

                st.caption(
                    f'{msg.get("provider","drift")} • confidence {msg.get("confidence",0):.2f}'
                )

    prompt = st.chat_input(
        "Ask Drift..."
    )

    if "pending_question" in st.session_state:

        prompt = st.session_state.pending_question
        del st.session_state.pending_question

    if prompt:

        st.session_state.messages.append({
            "role":"user",
            "content":prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):

            with st.spinner("Thinking..."):

                result = ask_ai(prompt)

                st.markdown(
                    result["answer"]
                )

                st.caption(
                    f'{result["provider"]} • confidence {result["confidence"]:.2f}'
                )

        st.session_state.messages.append({

            "role":"assistant",

            "content":result["answer"],

            "provider":result["provider"],

            "confidence":result["confidence"]

        })