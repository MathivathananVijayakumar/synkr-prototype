# =========================================================
# Synkr AI Dashboard - Fully Dynamic AI Version
# =========================================================

import streamlit as st
from groq import Groq
from st_supabase_connection import SupabaseConnection
import pandas as pd
import time
import json

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

    # =================================================
    # ANALYZE BUTTON
    # =================================================
    if st.button("Analyze Feedback"):

        if retro_text.strip():

            with st.spinner(
                "🤖 Synkr AI analyzing..."
            ):

                try:

                    start_time = time.time()

                    # =========================================
                    # DYNAMIC AI PROMPT
                    # =========================================
                    analysis_prompt = f"""
You are Synkr AI.

Analyze sprint retrospective feedback.

Return ONLY valid JSON.

Expected format:

{{
  "items": [
    {{
      "feedback": "string",
      "sentiment": "Positive | Neutral | Negative",
      "theme": "Deployment | Communication | Planning | Testing | Team Health | Delivery",
      "risk_level": "Low | Medium | High",
      "confidence": number,
      "insight": "short actionable insight"
    }}
  ]
}}

Rules:
- confidence between 50 and 95
- valid parsable JSON only
- no markdown
- no explanations outside JSON

Feedback:
{retro_text}
"""

                    # =========================================
                    # MODEL CALL
                    # =========================================
                    completion = (
                        client.chat.completions.create(
                            model="llama-3.1-8b-instant",
                            messages=[
                                {
                                    "role": "system",
                                    "content":
                                    "You are a JSON-only AI assistant."
                                },
                                {
                                    "role": "user",
                                    "content":
                                    analysis_prompt
                                }
                            ],
                            temperature=0.2,
                            max_tokens=1500
                        )
                    )

                    response_text = (
                        completion
                        .choices[0]
                        .message.content
                    )

                    latency = round(
                        time.time() - start_time,
                        2
                    )

                    # =========================================
                    # PARSE JSON
                    # =========================================
                    parsed = json.loads(
                        response_text
                    )

                    items = parsed["items"]

                    # =========================================
                    # SAVE CHAT HISTORY
                    # =========================================
                    conn.table("chat_history").insert({
                        "role": "user",
                        "content": retro_text
                    }).execute()

                    conn.table("chat_history").insert({
                        "role": "assistant",
                        "content": response_text
                    }).execute()

                    st.success(
                        "✅ AI Analysis Complete"
                    )

                    st.divider()

                    st.subheader(
                        "📋 AI Feedback Analysis"
                    )

                    # =========================================
                    # PROCESS AI OUTPUT
                    # =========================================
                    for item in items:

                        feedback = item["feedback"]

                        sentiment = item["sentiment"]

                        theme = item["theme"]

                        risk_level = item["risk_level"]

                        confidence = item["confidence"]

                        insight = item["insight"]

                        # =====================================
                        # SAVE ANALYSIS
                        # =====================================
                        conn.table(
                            "retro_analysis"
                        ).insert({

                            "sprint_name":
                            sprint_name,

                            "team_name":
                            team_name,

                            "feedback":
                            feedback,

                            "sentiment":
                            sentiment,

                            "theme":
                            theme,

                            "risk_level":
                            risk_level,

                            "confidence":
                            confidence

                        }).execute()

                        # =====================================
                        # SAVE METRICS
                        # =====================================
                        conn.table(
                            "ai_metrics"
                        ).insert({

                            "team_name":
                            team_name,

                            "latency":
                            latency,

                            "confidence":
                            confidence,

                            "hallucination_flag":
                            False,

                            "override_flag":
                            False

                        }).execute()

                        # =====================================
                        # GUARDRAILS
                        # =====================================
                        feedback_lower = (
                            feedback.lower()
                        )

                        if (
                            st.session_state
                            .guardrails[
                                "burnout_detection"
                            ]
                        ):

                            if any(
                                word in feedback_lower
                                for word in burnout_keywords
                            ):

                                conn.table(
                                    "guardrail_events"
                                ).insert({

                                    "sprint_name":
                                    sprint_name,

                                    "team_name":
                                    team_name,

                                    "feedback":
                                    feedback,

                                    "guardrail_type":
                                    "Burnout Detection",

                                    "severity":
                                    "Medium",

                                    "reviewer_required":
                                    True

                                }).execute()

                        if (
                            st.session_state
                            .guardrails[
                                "sensitive_hr"
                            ]
                        ):

                            if any(
                                word in feedback_lower
                                for word in sensitive_keywords
                            ):

                                conn.table(
                                    "guardrail_events"
                                ).insert({

                                    "sprint_name":
                                    sprint_name,

                                    "team_name":
                                    team_name,

                                    "feedback":
                                    feedback,

                                    "guardrail_type":
                                    "Sensitive HR Content",

                                    "severity":
                                    "High",

                                    "reviewer_required":
                                    True

                                }).execute()

                        if (
                            st.session_state
                            .guardrails[
                                "named_detection"
                            ]
                        ):

                            if "manager" in feedback_lower:

                                conn.table(
                                    "guardrail_events"
                                ).insert({

                                    "sprint_name":
                                    sprint_name,

                                    "team_name":
                                    team_name,

                                    "feedback":
                                    feedback,

                                    "guardrail_type":
                                    "Named Individual",

                                    "severity":
                                    "Medium",

                                    "reviewer_required":
                                    False

                                }).execute()

                        # =====================================
                        # UI DISPLAY
                        # =====================================
                        threshold = (
                            st.session_state
                            .guardrails[
                                "confidence_threshold"
                            ]
                        )

                        with st.container(border=True):

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
                                    "🔴 Manual Review Required"
                                )

                            st.write(
                                f"📝 {feedback}"
                            )

                            st.info(
                                f"💡 Insight: {insight}"
                            )

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
                                risk_level
                            )

                            col4.metric(
                                "Confidence",
                                f"{confidence}%"
                            )

                except Exception as e:

                    st.error(
                        f"AI Analysis Error: {e}"
                    )

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
            # SENTIMENT TRENDS
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

            st.subheader(
                "📝 Recent Sprint Feedback"
            )

            st.dataframe(
                df.tail(10),
                width="stretch"
            )

        else:

            st.info(
                "No dashboard data yet."
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
        "named_detection":
        named_detection,

        "burnout_detection":
        burnout_detection,

        "sensitive_hr":
        sensitive_hr,

        "confidence_threshold":
        confidence_threshold
    }

    st.success(
        "✅ Guardrails Updated"
    )

    st.divider()

    # =============================================
    # GUARDRAIL ANALYTICS
    # =============================================
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
                "Guardrail Distribution"
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

        else:

            st.info(
                "No guardrail events yet."
            )

    except Exception as e:

        st.error(
            f"Guardrail Error: {e}"
        )

# =================================================
# HITL REVIEW
# =================================================
if page == "🧠 HITL Review":

    st.title(
        "🧠 Human-in-the-Loop Review"
    )

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

                    col1, col2, col3 = (
                        st.columns(3)
                    )

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
                                "Deployment",
                                "Communication",
                                "Planning",
                                "Testing",
                                "Team Health",
                                "Delivery"
                            ],
                            key=f"theme_{index}"
                        )
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

        else:

            st.info(
                "No admin metrics yet."
            )

    except Exception as e:

        st.error(
            f"Admin Dashboard Error: {e}"
        )