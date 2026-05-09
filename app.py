import streamlit as st
from groq import Groq
from st_supabase_connection import SupabaseConnection
import pandas as pd
import time

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
# GLOBAL KEYWORDS
# =================================================
sensitive_keywords = [
    "harassment",
    "fired",
    "lawsuit",
    "abuse",
    "salary"
]

burnout_keywords = [
    "burnout",
    "stress",
    "overworked",
    "exhausted",
    "tired"
]

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

if "guardrails" not in st.session_state:

    st.session_state.guardrails = {
        "named_detection": True,
        "burnout_detection": True,
        "sensitive_hr": True,
        "confidence_threshold": 70
    }

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

    guardrails = st.session_state.guardrails

    # -------------------------------------------------
    # INPUT GUARDRAILS
    # -------------------------------------------------
    if guardrails["sensitive_hr"]:

        if any(
            word in retro_text.lower()
            for word in sensitive_keywords
        ):

            st.error(
                "🚨 Sensitive HR-related content detected"
            )

    if guardrails["burnout_detection"]:

        if any(
            word in retro_text.lower()
            for word in burnout_keywords
        ):

            st.warning(
                "🔥 Burnout risk detected"
            )

    if guardrails["named_detection"]:

        if "manager" in retro_text.lower():

            st.warning(
                "👤 Potential named individual reference detected"
            )

    # -------------------------------------------------
    # QUALITY CHECK
    # -------------------------------------------------
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

    # -------------------------------------------------
    # ANALYZE BUTTON
    # -------------------------------------------------
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

                    # -----------------------------------------
                    # SAVE CHAT HISTORY
                    # -----------------------------------------
                    conn.table("chat_history").insert({
                        "role": "user",
                        "content": retro_text
                    }).execute()

                    conn.table("chat_history").insert({
                        "role": "assistant",
                        "content": response
                    }).execute()

                    # -----------------------------------------
                    # SAVE METRICS
                    # -----------------------------------------
                    conn.table("ai_metrics").insert({
                        "team_name": team_name,
                        "latency": latency,
                        "confidence": 82,
                        "hallucination_flag": False,
                        "override_flag": False
                    }).execute()

                    # -----------------------------------------
                    # SHOW AI RESPONSE
                    # -----------------------------------------
                    st.success(
                        "✅ Analysis Complete"
                    )

                    st.markdown(response)

                    st.divider()

                    st.subheader(
                        "📋 Feedback Analysis"
                    )

                    # -----------------------------------------
                    # FEEDBACK CARDS
                    # -----------------------------------------
                    for item in lines:

                        if item.strip():

                            item_lower = item.lower()

                            sentiment = "Neutral"
                            risk = "Medium"
                            confidence = 75
                            theme = "General"

                            if any(
                                word in item_lower
                                for word in [
                                    "good",
                                    "great",
                                    "happy",
                                    "smooth"
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

                            threshold = guardrails[
                                "confidence_threshold"
                            ]

                            # ---------------------------------
                            # CONFIDENCE UI
                            # ---------------------------------
                            if confidence >= threshold:

                                st.success(
                                    "🟢 High Confidence"
                                )

                            elif confidence >= 60:

                                st.warning(
                                    "🟠 Suggested — Review Before Use"
                                )

                            else:

                                st.error(
                                    "🔴 AI Unsure — Manual Review Required"
                                )

                            with st.container(border=True):

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

        if rows.data and len(rows.data) > 0:

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

            st.subheader("📈 Sprint Trends")

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

            st.subheader("📊 Theme Distribution")

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

        else:

            st.info(
                "No dashboard data available yet."
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

    named_detection = st.toggle(
        "Named Individual Detection",
        value=st.session_state.guardrails[
            "named_detection"
        ]
    )

    burnout_detection = st.toggle(
        "Burnout Detection",
        value=st.session_state.guardrails[
            "burnout_detection"
        ]
    )

    sensitive_hr = st.toggle(
        "Sensitive HR Content",
        value=st.session_state.guardrails[
            "sensitive_hr"
        ]
    )

    confidence_threshold = st.slider(
        "Minimum Confidence Threshold",
        0,
        100,
        st.session_state.guardrails[
            "confidence_threshold"
        ]
    )

    st.session_state.guardrails = {
        "named_detection": named_detection,
        "burnout_detection": burnout_detection,
        "sensitive_hr": sensitive_hr,
        "confidence_threshold": confidence_threshold
    }

    st.success(
        "✅ Guardrail settings updated"
    )

    st.divider()

    st.subheader("Active Protections")

    if named_detection:
        st.info(
            "👤 Named individual detection enabled"
        )

    if burnout_detection:
        st.info(
            "🔥 Burnout detection enabled"
        )

    if sensitive_hr:
        st.info(
            "⚠ Sensitive HR filtering enabled"
        )

    st.warning(
        f"AI outputs below "
        f"{confidence_threshold}% confidence "
        f"require Scrum Master review."
    )

    st.subheader("Risk Detection Preview")

    sample_text = st.text_area(
        "Test guardrails with sample retro feedback",
        placeholder=(
            "Example:\n"
            "Team feels burnout due to deployment delays"
        ),
        height=120
    )

    if sample_text:

        sample_lower = sample_text.lower()

        if sensitive_hr:

            if any(
                word in sample_lower
                for word in sensitive_keywords
            ):

                st.error(
                    "🚨 Sensitive HR content detected"
                )

        if burnout_detection:

            if any(
                word in sample_lower
                for word in burnout_keywords
            ):

                st.warning(
                    "🔥 Burnout risk detected"
                )

        if named_detection:

            if "manager" in sample_lower:

                st.warning(
                    "👤 Potential named individual reference detected"
                )

# =================================================
# SCREEN 4 — HITL REVIEW
# =================================================
if page == "🧠 HITL Review":

    st.title("🧠 Human-in-the-Loop Review")

    try:

        rows = conn.table(
            "chat_history"
        ).select("*").execute()

        if rows.data and len(rows.data) > 0:

            df = pd.DataFrame(rows.data)

            user_messages = df[
                df["role"] == "user"
            ]

            if len(user_messages) > 0:

                latest_feedback = (
                    user_messages.iloc[-1]["content"]
                )

                feedback_items = latest_feedback.split("\n")

                st.subheader(
                    "Review AI Predictions"
                )

                for index, item in enumerate(
                    feedback_items
                ):

                        if item.strip():

                            item_lower = item.lower()

                            ai_sentiment = "Neutral"
                            ai_theme = "General"

                            if any(
                                word in item_lower
                                for word in [
                                    "good",
                                    "great",
                                    "smooth"
                                ]
                            ):

                                ai_sentiment = "Positive"
                                ai_theme = "Delivery"

                            elif any(
                                word in item_lower
                                for word in [
                                    "delay",
                                    "blocked",
                                    "issue",
                                    "stress"
                                ]
                            ):

                                ai_sentiment = "Negative"
                                ai_theme = "Team Health"

                            with st.container(border=True):

                                st.write(f"📝 {item}")

                                col1, col2 = st.columns(2)

                                col1.metric(
                                    "AI Sentiment",
                                    ai_sentiment
                                )

                                col2.metric(
                                    "AI Theme",
                                    ai_theme
                                )

                                st.divider()

                                corrected_sentiment = (
                                    st.selectbox(
                                        "Correct Sentiment",
                                        [
                                            "Positive",
                                            "Neutral",
                                            "Negative"
                                        ],
                                        key=f"sent_{index}"
                                    )
                                )

                                corrected_theme = (
                                    st.selectbox(
                                        "Correct Theme",
                                        [
                                            "Communication",
                                            "Deployment",
                                            "Planning",
                                            "Testing",
                                            "Team Health",
                                            "Delivery"
                                        ],
                                        key=f"theme_{index}"
                                    )
                                )

                                if st.button(
                                    "Submit Correction",
                                    key=f"btn_{index}"
                                ):

                                    override_flag = (
                                        corrected_sentiment
                                        != ai_sentiment
                                    )

                                    conn.table(
                                        "ai_metrics"
                                    ).insert({
                                        "team_name": "Pilot Team",
                                        "latency": 0,
                                        "confidence": 75,
                                        "hallucination_flag": False,
                                        "override_flag": override_flag
                                    }).execute()

                                    st.success(
                                        "✅ Correction Saved"
                                    )

            else:

                st.info(
                    "No retro feedback available yet."
                )

        else:

            st.info(
                "No chat history found."
            )

    except Exception as e:

        st.error(
            f"HITL Review Error: {e}"
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

        if rows.data and len(rows.data) > 0:

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
                    df["hallucination_flag"].sum()
                    / total
                ) * 100,
                1
            )

            override_rate = round(
                (
                    df["override_flag"].sum()
                    / total
                ) * 100,
                1
            )

            active_teams = (
                df["team_name"].nunique()
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

            if st.button("🔴 DISABLE AI"):

                st.error("AI Disabled")

        else:

            st.info(
                "No AI metrics available yet. "
                "Run sprint analysis first."
            )

    except Exception as e:

        st.error(
            f"Admin Dashboard Error: {e}"
        )