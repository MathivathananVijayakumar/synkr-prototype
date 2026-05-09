import streamlit as st
from groq import Groq
from st_supabase_connection import SupabaseConnection
import pandas as pd
import json

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Synkr - Sprint Retrospective AI",
    page_icon="🤖",
    layout="wide"
)

# -------------------------------------------------
# TITLE
# -------------------------------------------------
st.title("🤖 Synkr: Sprint Retrospective AI Assistant")
st.caption(
    "AI-powered sprint retrospective sentiment and risk analyzer"
)

# -------------------------------------------------
# SUPABASE CONNECTION
# -------------------------------------------------
conn = st.connection(
    "supabase",
    type=SupabaseConnection,
    url=st.secrets["SUPABASE_URL"],
    key=st.secrets["SUPABASE_KEY"]
)

# -------------------------------------------------
# GROQ CLIENT
# -------------------------------------------------
client = Groq(
    api_key=st.secrets["GROQ_API_KEY"]
)

# -------------------------------------------------
# SYSTEM PROMPT
# -------------------------------------------------
system_prompt = """
You are Synkr AI, an Agile Sprint Retrospective Assistant.

Your responsibilities:
- Analyze sprint retrospective feedback
- Detect sentiment
- Detect recurring themes
- Identify delivery risks
- Detect burnout or communication issues
- Provide concise actionable insights
- Speak conversationally like an Agile coach

Rules:
- Be concise and professional
- Never hallucinate
- Mention uncertainty when confidence is low
- Focus on sprint improvement
- Keep responses practical and actionable
"""

# -------------------------------------------------
# LOAD CHAT HISTORY
# -------------------------------------------------
if "messages" not in st.session_state:

    try:

        rows = conn.table("chat_history") \
            .select("*") \
            .order("id") \
            .execute()

        if rows.data and len(rows.data) > 0:

            st.session_state.messages = [
                {
                    "role": row["role"],
                    "content": row["content"]
                }
                for row in rows.data
            ]

        else:

            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": (
                        "Hi 👋 I'm Synkr AI.\n\n"
                        "Paste sprint retrospective feedback "
                        "or ask me about sprint/team health."
                    )
                }
            ]

    except Exception as e:

        st.error(f"Error loading history: {e}")

        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hi 👋 I'm Synkr AI."
            }
        ]

# -------------------------------------------------
# SIDEBAR DASHBOARD
# -------------------------------------------------
with st.sidebar:

    st.header("📊 Sprint Health")

    try:

        rows = conn.table("chat_history") \
            .select("*") \
            .execute()

        if rows.data:

            df = pd.DataFrame(rows.data)

            total_msgs = len(df)

            st.metric(
                "Total Messages",
                total_msgs
            )

            risk_keywords = [
                "burnout",
                "delay",
                "blocked",
                "stress",
                "issue",
                "late",
                "problem"
            ]

            risk_count = 0

            for text in df["content"]:

                text = str(text).lower()

                if any(
                    word in text
                    for word in risk_keywords
                ):
                    risk_count += 1

            st.metric(
                "Risk Signals",
                risk_count
            )

            st.metric(
                "AI Status",
                "Active"
            )

    except Exception as e:

        st.warning("Dashboard unavailable")

# -------------------------------------------------
# DISPLAY CHAT HISTORY
# -------------------------------------------------
for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

# -------------------------------------------------
# CHAT INPUT
# -------------------------------------------------
prompt = st.chat_input(
    "Paste sprint retro feedback or ask Synkr AI..."
)

# -------------------------------------------------
# PROCESS INPUT
# -------------------------------------------------
if prompt:

    # ---------------------------------------------
    # USER MESSAGE
    # ---------------------------------------------
    user_message = {
        "role": "user",
        "content": prompt
    }

    st.session_state.messages.append(user_message)

    # DISPLAY USER MESSAGE
    with st.chat_message("user"):

        st.markdown(prompt)

    # SAVE USER MESSAGE
    try:

        conn.table("chat_history").insert({
            "role": "user",
            "content": prompt
        }).execute()

    except Exception as e:

        st.warning("Could not save user message")

    # ---------------------------------------------
    # AI RESPONSE
    # ---------------------------------------------
    with st.chat_message("assistant"):

        with st.spinner("🤖 Synkr AI analyzing sprint feedback..."):

            try:

                messages = [
                    {
                        "role": "system",
                        "content": system_prompt
                    }
                ] + st.session_state.messages

                completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=messages,
                    temperature=0.4,
                    max_tokens=1024
                )

                response = (
                    completion
                    .choices[0]
                    .message
                    .content
                )

                st.markdown(response)

                assistant_message = {
                    "role": "assistant",
                    "content": response
                }

                st.session_state.messages.append(
                    assistant_message
                )

                # SAVE AI RESPONSE
                try:

                    conn.table("chat_history").insert({
                        "role": "assistant",
                        "content": response
                    }).execute()

                except Exception as e:

                    st.warning(
                        "Could not save AI response"
                    )

            except Exception as e:

                st.error(f"AI Error: {e}")

# -------------------------------------------------
# CLEAR CHAT
# -------------------------------------------------
st.divider()

col1, col2 = st.columns(2)

with col1:

    if st.button("🗑 Clear Chat History"):

        try:

            conn.table("chat_history") \
                .delete() \
                .neq("id", 0) \
                .execute()

            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": (
                        "Chat history cleared 👋"
                    )
                }
            ]

            st.rerun()

        except Exception as e:

            st.error(
                f"Error clearing chat: {e}"
            )

with col2:

    st.download_button(
        "📥 Export Chat",
        data=json.dumps(
            st.session_state.messages,
            indent=2
        ),
        file_name="synkr_chat_history.json",
        mime="application/json"
    )