import streamlit as st
from groq import Groq
from st_supabase_connection import SupabaseConnection
import pandas as pd

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Synkr AI Assistant",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Synkr AI Assistant")

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
# LOAD CHAT HISTORY FROM SUPABASE
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
                    "content": "Hi 👋 I'm Synkr AI. How can I help you today?"
                }
            ]

    except Exception as e:

        st.error(f"Error loading chat history: {e}")

        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hi 👋 I'm Synkr AI."
            }
        ]

# -------------------------------------------------
# DISPLAY CHAT HISTORY
# -------------------------------------------------
for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

# -------------------------------------------------
# USER INPUT
# -------------------------------------------------
prompt = st.chat_input("Type your message...")

if prompt:

    # ---------------------------------------------
    # USER MESSAGE
    # ---------------------------------------------
    user_message = {
        "role": "user",
        "content": prompt
    }

    st.session_state.messages.append(user_message)

    # SAVE USER MESSAGE TO SUPABASE
    conn.table("chat_history").insert({
        "role": "user",
        "content": prompt
    }).execute()

    # DISPLAY USER MESSAGE
    with st.chat_message("user"):
        st.markdown(prompt)

    # ---------------------------------------------
    # AI RESPONSE
    # ---------------------------------------------
    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            try:

                completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=st.session_state.messages,
                    temperature=0.7,
                    max_tokens=1024
                )

                response = completion.choices[0].message.content

                st.markdown(response)

                assistant_message = {
                    "role": "assistant",
                    "content": response
                }

                st.session_state.messages.append(
                    assistant_message
                )

                # SAVE AI RESPONSE TO SUPABASE
                conn.table("chat_history").insert({
                    "role": "assistant",
                    "content": response
                }).execute()

            except Exception as e:

                st.error(f"Error: {e}")

# -------------------------------------------------
# CLEAR CHAT BUTTON
# -------------------------------------------------
st.divider()

if st.button("🗑 Clear Chat History"):

    try:

        conn.table("chat_history") \
            .delete() \
            .neq("id", 0) \
            .execute()

        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Chat history cleared 👋"
            }
        ]

        st.rerun()

    except Exception as e:

        st.error(f"Error clearing chat: {e}")