# ================================
# Synkr AI Dashboard - app.py
# ================================

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
# KEYWORDS
# =================================================
sensitive_keywords = [
    "harassment",
    "salary",
    "abuse",
    "lawsuit",
    "fired"
]

burnout_keywords = [
    "burnout",
    "stress",
    "exhausted",
    "tired",
    "overworked"
]

positive_keywords = [
    "good",
    "great",
    "excellent",
    "smooth",
    "improved",
    "happy",
    "fast"
]

negative_keywords = [
    "delay",
    "blocked",
    "issue",
    "problem",
    "failure",
    "stress",
    "burnout"
]

# =================================================
# SYSTEM PROMPT
# =================================================
system_prompt = """
You are Synkr AI.

Analyze sprint retrospective feedback.

Identify:
- sentiment
- theme
- risk level
- actionable insight

Possible themes:
- Deployment
- Communication
- Planning
- Testing
- Team Health
- Delivery

Be concise and practical.
"""

# =================================================
# SESSION STATE
# =================================================
if "guardrails" not in st.session_state:

    st.session_state.guardrails = {
        "named_detection": True,
        "burnout_detection": True,
        "sensitive_hr": True,
        "confidence_threshold": 70
    }

# =================================================
# SIDEBAR
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
# RETRO ANALYSIS
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

    # =================================================
    # GUARDRAIL DETECTION
    # =================================================
    if retro_text:

        # ---------------------------------------------
        # Sensitive HR
        # ---------------------------------------------
        if (
            guardrails["sensitive_hr"]
            and any(
                word in retro_text.lower()
                for word in sensitive_keywords
            )
        ):

            st.error(
                "🚨 Sensitive HR-related content detected"
            )

            conn.table(
                "guardrail_events"
            ).insert({

                "sprint_name": sprint_name,
                "team_name": team_name,
                "feedback": retro_text,
                "guardrail_type": "Sensitive HR Content",
                "severity": "High",
                "reviewer_required": True

            }).execute()

        # ---------------------------------------------
        # Burnout
        # ---------------------------------------------
        if (
            guardrails["burnout_detection"]
            and any(
                word in retro_text.lower()
                for word in burnout_keywords
            )
        ):

            st.warning(
                "🔥 Burnout risk detected"
            )

            conn.table(
                "guardrail_events"
            ).insert({

                "sprint_name": sprint_name,
                "team_name": team_name,
                "feedback": retro_text,
                "guardrail_type": "Burnout Detection",
                "severity": "Medium",
                "reviewer_required": True

            }).execute()

        # ---------------------------------------------
        # Named Detection
        # ---------------------------------------------
        if (
            guardrails["named_detection"]
            and "manager" in retro_text.lower()
        ):

            st.warning(
                "👤 Potential named individual reference detected"
            )

            conn.table(
                "guardrail_events"
            ).insert({

                "sprint_name": sprint_name,
                "team_name": team_name,
                "feedback": retro_text,
                "guardrail_type": "Named Individual",
                "severity": "Medium",
                "reviewer_required": False

            }).execute()

    # =================================================
    # ANALYZE
    # =================================================
    if st.button("Analyze Feedback"):

        if retro_text.strip():

            with st.spinner(
                "🤖 Synkr AI analyzing..."
            ):

                try:

                    start_time = time.time()

                    completion = (
                        client.chat.completions.create(
                            model="llama-3.1-8b-instant",
                            messages=[
                                {
                                    "role": "system",
                                    "content": system_prompt
                                },
                                {
                                    "role": "user",
                                    "content": retro_text
                                }
                            ],
                            temperature=0.4,
                            max_tokens=1024
                        )
                    )

                    response = (
                        completion
                        .choices[0]
                        .message.content
                    )

                    latency = round(
                        time.time() - start_time,
                        2
                    )

                    # =========================================
                    # SAVE CHAT
                    # =========================================
                    conn.table("chat_history").insert({
                        "role": "user",
                        "content": retro_text
                    }).execute()

                    conn.table("chat_history").insert({
                        "role": "assistant",
                        "content": response
                    }).execute()

                    # =========================================
                    # SAVE METRICS
                    # =========================================
                    conn.table("ai_metrics").insert({
                        "team_name": team_name,
                        "latency": latency,
                        "confidence": 82,
                        "hallucination_flag": False,
                        "override_flag": False
                    }).execute()

                    st.success(
                        "✅ Analysis Complete"
                    )

                    st.markdown(response)

                    st.divider()

                    st.subheader(
                        "📋 Feedback Analysis"
                    )

                    lines = retro_text.split("\n")

                    for item in lines:

                        if item.strip():

                            item_lower = item.lower()

                            sentiment = "Neutral"
                            risk = "Medium"
                            confidence = 75
                            theme = "Delivery"

                            # =====================================
                            # THEME DETECTION
                            # =====================================
                            if "deploy" in item_lower:

                                theme = "Deployment"

                            elif "communicat" in item_lower:

                                theme = "Communication"

                            elif "plan" in item_lower:

                                theme = "Planning"

                            elif "test" in item_lower:

                                theme = "Testing"

                            elif any(
                                word in item_lower
                                for word in burnout_keywords
                            ):

                                theme = "Team Health"

                            # =====================================
                            # SENTIMENT
                            # =====================================
                            if any(
                                word in item_lower
                                for word in positive_keywords
                            ):

                                sentiment = "Positive"
                                risk = "Low"
                                confidence = 90

                            elif any(
                                word in item_lower
                                for word in negative_keywords
                            ):

                                sentiment = "Negative"
                                risk = "High"
                                confidence = 82

                            # =====================================
                            # SAVE ANALYSIS
                            # =====================================
                            conn.table(
                                "retro_analysis"
                            ).insert({

                                "sprint_name": sprint_name,
                                "team_name": team_name,
                                "feedback": item,
                                "sentiment": sentiment,
                                "theme": theme,
                                "risk_level": risk,
                                "confidence": confidence

                            }).execute()

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
# TEAM DASHBOARD
# =================================================
if page == "📊 Team Dashboard":

    st.title("📊 Team Health Dashboard")

    try:

        rows = conn.table(
            "retro_analysis"
        ).select("*").execute()

        if rows.data:

            df = pd.DataFrame(rows.data)

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Total Feedback",
                len(df)
            )

            col2.metric(
                "Positive Signals",
                len(
                    df[
                        df["sentiment"]
                        == "Positive"
                    ]
                )
            )

            col3.metric(
                "Negative Signals",
                len(
                    df[
                        df["sentiment"]
                        == "Negative"
                    ]
                )
            )

            col4.metric(
                "Burnout Risks",
                len(
                    df[
                        df["theme"]
                        == "Team Health"
                    ]
                )
            )

            st.divider()

            # =========================================
            # SPRINT SENTIMENT TRENDS
            # =========================================
            st.subheader(
                "📈 Sprint Sentiment Trends"
            )

            trend_df = (
                df.groupby(
                    ["sprint_name", "sentiment"]
                )
                .size()
                .unstack(fill_value=0)
            )

            st.line_chart(trend_df)

            # =========================================
            # THEME DISTRIBUTION
            # =========================================
            st.subheader(
                "📊 Theme Distribution"
            )

            theme_counts = (
                df["theme"]
                .value_counts()
            )

            st.bar_chart(theme_counts)

            # =========================================
            # RECENT FEEDBACK
            # =========================================
            st.subheader(
                "📝 Recent Sprint Feedback"
            )

            st.dataframe(
                df.tail(10),
                width="stretch"
            )

    except Exception as e:

        st.error(
            f"Dashboard Error: {e}"
        )

# =================================================
# GUARDRAILS
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
        "✅ Guardrails Updated"
    )

    st.divider()

    sample_text = st.text_area(
        "Test guardrails",
        key="guardrail_test"
    )

    if sample_text:

        if any(
            word in sample_text.lower()
            for word in burnout_keywords
        ):

            st.warning(
                "🔥 Burnout risk detected"
            )

        if any(
            word in sample_text.lower()
            for word in sensitive_keywords
        ):

            st.error(
                "🚨 Sensitive HR content detected"
            )

        if "manager" in sample_text.lower():

            st.warning(
                "👤 Named individual detected"
            )

    st.divider()

    # =============================================
    # GUARDRAIL ANALYTICS
    # =============================================
    st.subheader(
        "📊 Guardrail Analytics"
    )

    try:

        guardrail_rows = conn.table(
            "guardrail_events"
        ).select("*").execute()

        if guardrail_rows.data:

            guardrail_df = pd.DataFrame(
                guardrail_rows.data
            )

            st.metric(
                "Total Guardrail Events",
                len(guardrail_df)
            )

            st.subheader(
                "Guardrail Type Distribution"
            )

            guardrail_counts = (
                guardrail_df[
                    "guardrail_type"
                ]
                .value_counts()
            )

            st.bar_chart(
                guardrail_counts
            )

            st.subheader(
                "Recent Guardrail Events"
            )

            st.dataframe(
                guardrail_df.tail(10),
                width="stretch"
            )

    except Exception as e:

        st.error(
            f"Guardrail Analytics Error: {e}"
        )

# =================================================
# HITL REVIEW
# =================================================
if page == "🧠 HITL Review":

    st.title("🧠 Human-in-the-Loop Review")

    try:

        rows = conn.table(
            "retro_analysis"
        ).select("*").execute()

        if rows.data:

            df = pd.DataFrame(rows.data)

            latest = df.tail(5)

            for index, row in latest.iterrows():

                with st.container(border=True):

                    st.write(
                        row["feedback"]
                    )

                    col1, col2, col3 = st.columns(3)

                    col1.metric(
                        "Sentiment",
                        row["sentiment"]
                    )

                    col2.metric(
                        "Theme",
                        row["theme"]
                    )

                    col3.metric(
                        "Confidence",
                        f"{row['confidence']}%"
                    )

                    corrected_sentiment = st.selectbox(
                        "Correct Sentiment",
                        [
                            "Positive",
                            "Neutral",
                            "Negative"
                        ],
                        key=f"sent_{index}"
                    )

                    corrected_theme = st.selectbox(
                        "Correct Theme",
                        [
                            "Deployment",
                            "Communication",
                            "Planning",
                            "Testing",
                            "Team Health",
                            "Delivery"
                        ],
                        key=f"theme_{index}"
                    )

                    if st.button(
                        "Submit Review",
                        key=f"review_{index}"
                    ):

                        conn.table(
                            "hitl_reviews"
                        ).insert({

                            "feedback":
                            row["feedback"],

                            "ai_sentiment":
                            row["sentiment"],

                            "corrected_sentiment":
                            corrected_sentiment,

                            "ai_theme":
                            row["theme"],

                            "corrected_theme":
                            corrected_theme,

                            "reviewer":
                            "Reviewer",

                            "status":
                            "Reviewed"

                        }).execute()

                        st.success(
                            "✅ Review Submitted"
                        )

    except Exception as e:

        st.error(
            f"HITL Error: {e}"
        )

# =================================================
# FEEDBACK SURVEY
# =================================================
if page == "📝 Feedback Survey":

    st.title("📝 Feedback Survey")

    theme_match = st.radio(
        "Did AI themes match discussions?",
        [
            "Yes",
            "Partially",
            "No"
        ]
    )

    usefulness = st.slider(
        "Insight usefulness",
        1,
        5,
        3
    )

    missed_feedback = st.text_area(
        "What did AI miss?"
    )

    if st.button(
        "Submit Feedback"
    ):

        conn.table(
            "feedback_survey"
        ).insert({

            "theme_match":
            theme_match,

            "usefulness":
            usefulness,

            "missed_feedback":
            missed_feedback

        }).execute()

        st.success(
            "✅ Feedback Submitted"
        )

# =================================================
# ADMIN DASHBOARD
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

            override_rate = round(
                (
                    df["override_flag"].sum()
                    / total
                ) * 100,
                1
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Model Confidence",
                f"{avg_confidence}%"
            )

            col2.metric(
                "Avg Latency",
                f"{avg_latency}s"
            )

            col3.metric(
                "Override Rate",
                f"{override_rate}%"
            )

            st.divider()

            st.subheader(
                "📊 AI Confidence Trend"
            )

            confidence_df = (
                df.groupby("team_name")[
                    "confidence"
                ]
                .mean()
            )

            st.bar_chart(confidence_df)

    except Exception as e:

        st.error(
            f"Admin Dashboard Error: {e}"
        )