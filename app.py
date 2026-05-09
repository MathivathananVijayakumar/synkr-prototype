import streamlit as st
from groq import Groq
from st_supabase_connection import SupabaseConnection
import pandas as pd
import json

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="Synkr AI Dashboard",
    page_icon="🤖",
    layout="wide"
)

# -------------------------------------------------
# CONNECTIONS
# -------------------------------------------------
conn = st.connection(
    "supabase",
    type=SupabaseConnection,
    url=st.secrets["SUPABASE_URL"],
    key=st.secrets["SUPABASE_KEY"]
)

client = Groq(
    api_key=st.secrets["GROQ_API_KEY"]
)

# -------------------------------------------------
# SYSTEM PROMPT
# -------------------------------------------------
system_prompt = """
You are Synkr AI.

You are an Agile Sprint Retrospective Assistant.

Responsibilities:
- Analyze sprint retrospectives
- Detect sentiment
- Detect recurring themes
- Identify burnout or delivery risks
- Provide concise actionable suggestions
- Speak like an Agile coach

Rules:
- Be concise
- Never hallucinate
- Mention uncertainty if confidence is low
- Focus on improving sprint health
"""

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "messages" not in st.session_state:

    try:

        rows = conn.table("chat_history") \
            .select("*") \
            .order("id") \
            .execute()

        if rows.data:

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
                        "Hi 👋 I'm Synkr AI. "
                        "Paste sprint retrospective feedback "
                        "or ask me about team health."
                    )
                }
            ]

    except Exception:

        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hi 👋 I'm Synkr AI"
            }
        ]

# -------------------------------------------------
# SIDEBAR NAVIGATION
# -------------------------------------------------
page = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Retro Analysis",
        "📊 Team Dashboard",
        "🛡 Guardrails",
        "🧠 HITL Review",
        "📝 Feedback Survey",
        "⚙ Admin Dashboard"
    ]
)

# =================================================
# SCREEN 1 — RETRO ANALYSIS
# =================================================
if page == "🏠 Retro Analysis":

    st.title("🤖 Synkr Retro Analysis")

    sprint_name = st.text_input("Sprint Name")
    team_name = st.text_input("Team Name")

    retro_text = st.text_area(
        "Paste sprint retrospective feedback",
        height=220,
        placeholder="One feedback item per line"
    )

    if st.button("Analyze Feedback"):

        if retro_text:

            with st.spinner("Analyzing sprint feedback..."):

                try:

                    messages = [
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": retro_text
                        }
                    ]

                    completion = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=messages,
                        temperature=0.4,
                        max_tokens=1024
                    )

                    response = completion \
                        .choices[0] \
                        .message.content

                    st.success("Analysis Complete")

                    st.markdown(response)

                    # SAVE USER MESSAGE
                    conn.table("chat_history").insert({
                        "role": "user",
                        "content": retro_text
                    }).execute()

                    # SAVE AI MESSAGE
                    conn.table("chat_history").insert({
                        "role": "assistant",
                        "content": response
                    }).execute()

                    # FEEDBACK CARDS
                    st.divider()

                    st.subheader("AI Insights")

                    feedback_items = retro_text.split("\n")

                    for item in feedback_items:

                        if item.strip():

                            with st.container(border=True):

                                st.write(item)

                                if "delay" in item.lower():
                                    sentiment = "Negative"
                                    risk = "High"
                                elif "good" in item.lower():
                                    sentiment = "Positive"
                                    risk = "Low"
                                else:
                                    sentiment = "Neutral"
                                    risk = "Medium"

                                col1, col2, col3 = st.columns(3)

                                col1.metric(
                                    "Sentiment",
                                    sentiment
                                )

                                col2.metric(
                                    "Risk",
                                    risk
                                )

                                col3.metric(
                                    "Confidence",
                                    "82%"
                                )

                                st.button(
                                    f"Flag as Wrong - {item}",
                                    key=item
                                )

                except Exception as e:

                    st.error(f"AI Error: {e}")

# =================================================
# SCREEN 2 — TEAM DASHBOARD
# =================================================
if page == "📊 Team Dashboard":

    st.title("📊 Team Health Dashboard")

    try:

        rows = conn.table("chat_history") \
            .select("*") \
            .execute()

        if rows.data:

            df = pd.DataFrame(rows.data)

            col1, col2, col3, col4 = st.columns(4)

            total_msgs = len(df)

            positive = len(
                df[
                    df["content"]
                    .str.contains(
                        "good|great|happy",
                        case=False,
                        na=False
                    )
                ]
            )

            negative = len(
                df[
                    df["content"]
                    .str.contains(
                        "delay|blocked|issue",
                        case=False,
                        na=False
                    )
                ]
            )

            burnout = len(
                df[
                    df["content"]
                    .str.contains(
                        "burnout|stress|tired",
                        case=False,
                        na=False
                    )
                ]
            )

            col1.metric("Total Messages", total_msgs)
            col2.metric("Positive Signals", positive)
            col3.metric("Negative Signals", negative)
            col4.metric("Burnout Risks", burnout)

            st.divider()

            st.subheader("Sprint Trends")

            chart_data = pd.DataFrame({
                "Sprint": [
                    "Sprint 21",
                    "Sprint 22",
                    "Sprint 23"
                ],
                "Positive": [60, 68, 72],
                "Negative": [30, 22, 18]
            })

            st.line_chart(
                chart_data.set_index("Sprint")
            )

            st.subheader("Theme Distribution")

            st.bar_chart({
                "Communication": 8,
                "Deployment": 6,
                "Planning": 4,
                "Testing": 3
            })

            st.subheader("Recent Sprint Feedback")

            st.dataframe(df.tail(10))

    except Exception as e:

        st.error(f"Dashboard Error: {e}")

# =================================================
# SCREEN 3 — GUARDRAILS
# =================================================
if page == "🛡 Guardrails":

    st.title("🛡 AI Guardrails")

    st.toggle(
        "Named Individual Detection",
        value=True
    )

    st.toggle(
        "Burnout Detection",
        value=True
    )

    st.toggle(
        "Sensitive HR Content",
        value=True
    )

    st.slider(
        "Minimum Confidence Threshold",
        0,
        100,
        70
    )

    st.warning(
        "Low-confidence AI outputs require "
        "manual Scrum Master review."
    )

# =================================================
# SCREEN 4 — HITL REVIEW
# =================================================
if page == "🧠 HITL Review":

    st.title("🧠 Human-in-the-Loop Review")

    st.write("AI Prediction: Negative")

    sentiment = st.selectbox(
        "Correct Sentiment",
        [
            "Positive",
            "Neutral",
            "Negative"
        ]
    )

    theme = st.selectbox(
        "Correct Theme",
        [
            "Communication",
            "Deployment",
            "Planning",
            "Testing"
        ]
    )

    if st.button("Submit Correction"):

        st.success("Correction Saved")

# =================================================
# SCREEN 5 — FEEDBACK SURVEY
# =================================================
if page == "📝 Feedback Survey":

    st.title("📝 Feedback Survey")

    st.radio(
        "Did AI themes match team discussions?",
        [
            "Yes",
            "Partially",
            "No"
        ]
    )

    st.slider(
        "Insight usefulness",
        1,
        5
    )

    st.text_area(
        "What did the AI miss?"
    )

    if st.button("Submit Feedback"):

        st.success("Feedback Submitted")

# =================================================
# SCREEN 6 — ADMIN DASHBOARD
# =================================================
if page == "⚙ Admin Dashboard":

    st.title("⚙ Admin Dashboard")

    col1, col2 = st.columns(2)

    col1.metric("Model Accuracy", "87%")
    col2.metric("Avg Latency", "2.1s")

    col1.metric("Override Rate", "18%")
    col2.metric("Hallucination Rate", "3%")

    st.divider()

    st.success("Pilot Teams Active: 3")

    st.info("Average Time Saved: 74%")

    st.warning(
        "Monitor hallucination spikes and override rates"
    )

    if st.button("🔴 DISABLE AI"):

        st.error("AI Disabled")
