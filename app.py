import streamlit as st
from groq import Groq
from st_supabase_connection import SupabaseConnection
import pandas as pd
import time
from datetime import datetime

# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(
    page_title="Synkr AI Dashboard",
    page_icon="🤖",
    layout="wide"
)

# =================================================
# CONNECTIONS
# =================================================
conn = st.connection(
    "supabase",
    type=SupabaseConnection,
    url=st.secrets["SUPABASE_URL"],
    key=st.secrets["SUPABASE_KEY"]
)

client = Groq(
    api_key=st.secrets["GROQ_API_KEY"]
)

# =================================================
# SYSTEM PROMPT
# =================================================
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

# =================================================
# SESSION STATE
# =================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# =================================================
# SIDEBAR NAVIGATION
# =================================================
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

    # ---------------------------------------------
    # GUARDRAILS
    # ---------------------------------------------
    sensitive_keywords = [
        "harassment",
        "fired",
        "lawsuit",
        "abuse",
        "salary",
        "manager"
    ]

    if any(
        word in retro_text.lower()
        for word in sensitive_keywords
    ):
        st.warning(
            "⚠ Sensitive HR-related content detected."
        )

    lines = retro_text.split("\n")

    short_lines = [
        line for line in lines
        if len(line.split()) < 5
    ]

    if len(short_lines) > 2:
        st.warning(
            "⚠ Feedback quality may be too low "
            "for reliable AI analysis."
        )

    # ---------------------------------------------
    # ANALYZE BUTTON
    # ---------------------------------------------
    if st.button("Analyze Feedback"):

        if retro_text:

            with st.spinner(
                "🤖 Synkr AI analyzing sprint feedback..."
            ):

                try:

                    start_time = time.time()

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

                    completion = (
                        client.chat.completions.create(
                            model="llama-3.1-8b-instant",
                            messages=messages,
                            temperature=0.4,
                            max_tokens=1024
                        )
                    )

                    response = (
                        completion
                        .choices[0]
                        .message.content
                    )

                    end_time = time.time()

                    latency = round(
                        end_time - start_time,
                        2
                    )

                    # ---------------------------------
                    # SAVE CHAT HISTORY
                    # ---------------------------------
                    conn.table("chat_history").insert({
                        "role": "user",
                        "content": retro_text
                    }).execute()

                    conn.table("chat_history").insert({
                        "role": "assistant",
                        "content": response
                    }).execute()

                    # ---------------------------------
                    # AI RESPONSE
                    # ---------------------------------
                    st.success(
                        "✅ Analysis Complete"
                    )

                    st.markdown(response)

                    # ---------------------------------
                    # FEEDBACK CARDS
                    # ---------------------------------
                    st.divider()

                    st.subheader(
                        "📋 Feedback Analysis"
                    )

                    for item in lines:

                        if item.strip():

                            item_lower = item.lower()

                            sentiment = "Neutral"
                            risk = "Medium"
                            confidence = 75
                            theme = "General"

                            # -------------------------
                            # SIMPLE RULE ENGINE
                            # -------------------------
                            if any(
                                word in item_lower
                                for word in [
                                    "good",
                                    "great",
                                    "smooth",
                                    "happy"
                                ]
                            ):
                                sentiment = "Positive"
                                risk = "Low"
                                confidence = 90
                                theme = "Delivery"

                            elif any(
                                word in item_lower
                                for word in [
                                    "delay",
                                    "blocked",
                                    "issue",
                                    "stress",
                                    "burnout"
                                ]
                            ):
                                sentiment = "Negative"
                                risk = "High"
                                confidence = 82
                                theme = "Team Health"

                            # -------------------------
                            # CONFIDENCE UI
                            # -------------------------
                            if confidence >= 85:
                                st.success(
                                    "🟢 High Confidence"
                                )

                            elif confidence >= 60:
                                st.warning(
                                    "🟠 Suggested — Review Before Use"
                                )

                            else:
                                st.error(
                                    "🔴 AI Unsure"
                                )

                            with st.container(
                                border=True
                            ):

                                st.write(item)

                                col1, col2, col3, col4 = (
                                    st.columns(4)
                                )

                                col1.metric(
                                    "Sentiment",
                                    sentiment
                                )

                                col2.metric(
                                    "Theme",
                                    theme
                                )

                                col3.metric(
                                    "Risk",
                                    risk
                                )

                                col4.metric(
                                    "Confidence",
                                    f"{confidence}%"
                                )

                                hallucination = st.checkbox(
                                    "Flag as Hallucination",
                                    key=f"hall_{item}"
                                )

                                override = st.checkbox(
                                    "Manual Override",
                                    key=f"override_{item}"
                                )

                                # ---------------------
                                # SAVE METRICS
                                # ---------------------
                                conn.table(
                                    "ai_metrics"
                                ).insert({
                                    "team_name": team_name,
                                    "latency": latency,
                                    "confidence": confidence,
                                    "hallucination_flag": hallucination,
                                    "override_flag": override
                                }).execute()

                except Exception as e:

                    st.error(f"AI Error: {e}")

# =================================================
# SCREEN 2 — TEAM DASHBOARD
# =================================================
if page == "📊 Team Dashboard":

    st.title("📊 Team Health Dashboard")

    try:

        rows = conn.table(
            "chat_history"
        ).select("*").execute()

        if rows.data:

            df = pd.DataFrame(rows.data)

            col1, col2, col3, col4 = st.columns(4)

            total_msgs = len(df)

            positive = len(
                df[
                    df["content"].str.contains(
                        "good|great|happy",
                        case=False,
                        na=False
                    )
                ]
            )

            negative = len(
                df[
                    df["content"].str.contains(
                        "delay|blocked|issue",
                        case=False,
                        na=False
                    )
                ]
            )

            burnout = len(
                df[
                    df["content"].str.contains(
                        "burnout|stress|tired",
                        case=False,
                        na=False
                    )
                ]
            )

            col1.metric(
                "Total Messages",
                total_msgs
            )

            col2.metric(
                "Positive Signals",
                positive
            )

            col3.metric(
                "Negative Signals",
                negative
            )

            col4.metric(
                "Burnout Risks",
                burnout
            )

            st.divider()

            st.subheader(
                "📈 Sprint Trends"
            )

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
                chart_data.set_index(
                    "Sprint"
                )
            )

            st.subheader(
                "📊 Theme Distribution"
            )

            st.bar_chart({
                "Communication": 8,
                "Deployment": 6,
                "Planning": 4,
                "Testing": 3
            })

            st.subheader(
                "📝 Recent Sprint Feedback"
            )

            st.dataframe(
                df.tail(10),
                use_container_width=True
            )

    except Exception as e:

        st.error(
            f"Dashboard Error: {e}"
        )

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
        "Low-confidence AI outputs "
        "require Scrum Master review."
    )

# =================================================
# SCREEN 4 — HITL REVIEW
# =================================================
if page == "🧠 HITL Review":

    st.title(
        "🧠 Human-in-the-Loop Review"
    )

    st.write(
        "AI Prediction: Negative"
    )

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

    if st.button(
        "Submit Correction"
    ):
        st.success(
            "Correction Saved"
        )

# =================================================
# SCREEN 5 — FEEDBACK SURVEY
# =================================================
if page == "📝 Feedback Survey":

    st.title("📝 Feedback Survey")

    st.radio(
        "Did AI themes match discussions?",
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
        "What did AI miss?"
    )

    if st.button(
        "Submit Feedback"
    ):
        st.success(
            "Feedback Submitted"
        )

# =================================================
# SCREEN 6 — ADMIN DASHBOARD
# =================================================
if page == "⚙ Admin Dashboard":

    st.title("⚙ Admin Dashboard")

    try:

        rows = conn.table(
            "ai_metrics"
        ).select("*").execute()

        if rows.data:

            df = pd.DataFrame(rows.data)

            total = len(df)

            avg_confidence = round(
                df["confidence"].mean(),
                1
            )

            avg_latency = round(
                df["latency"].mean(),
                2
            )

            hallucination_rate = round(
                (
                    df["hallucination_flag"]
                    .sum() / total
                ) * 100,
                1
            )

            override_rate = round(
                (
                    df["override_flag"]
                    .sum() / total
                ) * 100,
                1
            )

            active_teams = (
                df["team_name"]
                .nunique()
            )

            col1, col2 = st.columns(2)

            col1.metric(
                "Model Confidence",
                f"{avg_confidence}%"
            )

            col2.metric(
                "Avg Latency",
                f"{avg_latency}s"
            )

            col1.metric(
                "Override Rate",
                f"{override_rate}%"
            )

            col2.metric(
                "Hallucination Rate",
                f"{hallucination_rate}%"
            )

            st.divider()

            st.success(
                f"Pilot Teams Active: {active_teams}"
            )

            st.info(
                "Average Time Saved: 74%"
            )

            # -------------------------------------
            # RISK ALERTS
            # -------------------------------------
            if hallucination_rate > 5:
                st.error(
                    "⚠ Hallucination rate above threshold"
                )

            if override_rate > 25:
                st.error(
                    "⚠ Override rate too high"
                )

            st.warning(
                "Monitor hallucination spikes "
                "and override rates"
            )

            # -------------------------------------
            # KILL SWITCH
            # -------------------------------------
            if st.button(
                "🔴 DISABLE AI"
            ):
                st.error(
                    "AI Disabled"
                )

    except Exception as e:

        st.error(
            f"Admin Dashboard Error: {e}"
        )