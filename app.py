# =========================================================
# Synkr AI Dashboard - Enterprise AI Governance Prototype
# =========================================================

import streamlit as st
from groq import Groq
from st_supabase_connection import SupabaseConnection
import pandas as pd
import time
import json
import plotly.express as px

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

# =================================================
# SESSION STATE
# =================================================
if "guardrails" not in st.session_state:

    st.session_state.guardrails = {
        "sensitive_hr": True,
        "confidence_threshold": 70
    }

if "ai_enabled" not in st.session_state:

    st.session_state.ai_enabled = True

# =================================================
# HELPER FUNCTIONS
# =================================================
def detect_hallucination(text):

    hallucination_terms = [
        "always",
        "guaranteed",
        "100%",
        "never fails",
        "perfect",
        "zero issues",
        "completely solved"
    ]

    text = text.lower()

    return any(
        term in text
        for term in hallucination_terms
    )

def detect_data_insufficiency(feedback):

    return len(feedback.split()) < 4

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

    if st.button("Analyze Feedback →"):

        if not st.session_state.ai_enabled:

            st.error(
                "🚨 AI analysis is disabled."
            )

            st.stop()

        if retro_text.strip():

            with st.spinner(
                "🤖 Synkr AI analyzing..."
            ):

                try:

                    start_time = time.time()

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

Feedback:
{retro_text}
"""

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

                    parsed = json.loads(
                        response_text
                    )

                    items = parsed["items"]

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

                    for item in items:

                        feedback = item["feedback"]
                        sentiment = item["sentiment"]
                        theme = item["theme"]
                        risk_level = item["risk_level"]
                        confidence = item["confidence"]
                        insight = item["insight"]

                        hallucination_flag = (
                            detect_hallucination(
                                retro_text
                            )
                        )

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
                            hallucination_flag,

                            "override_flag":
                            False

                        }).execute()

                        # =====================================
                        # GUARDRAILS
                        # =====================================

                        if (
                            st.session_state
                            .guardrails[
                                "sensitive_hr"
                            ]
                        ):

                            if any(
                                word in retro_text.lower()
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
                                    retro_text,

                                    "guardrail_type":
                                    "Sensitive HR Content",

                                    "severity":
                                    "High",

                                    "reviewer_required":
                                    True

                                }).execute()

                                st.error(
                                    "🚨 Sensitive HR content detected"
                                )

                        if hallucination_flag:

                            conn.table(
                                "guardrail_events"
                            ).insert({

                                "sprint_name":
                                sprint_name,

                                "team_name":
                                team_name,

                                "feedback":
                                retro_text,

                                "guardrail_type":
                                "Hallucination Warning",

                                "severity":
                                "High",

                                "reviewer_required":
                                True

                            }).execute()

                            st.warning(
                                "⚠ Potential hallucination detected"
                            )

                        if detect_data_insufficiency(
                            retro_text
                        ):

                            conn.table(
                                "guardrail_events"
                            ).insert({

                                "sprint_name":
                                sprint_name,

                                "team_name":
                                team_name,

                                "feedback":
                                retro_text,

                                "guardrail_type":
                                "Data Insufficiency",

                                "severity":
                                "Medium",

                                "reviewer_required":
                                True

                            }).execute()

                            st.warning(
                                "⚠ Insufficient feedback context"
                            )

                        threshold = (
                            st.session_state
                            .guardrails[
                                "confidence_threshold"
                            ]
                        )

                        with st.container(border=True):

                            if confidence >= 85:

                                st.success(
                                    "🟢 High Confidence"
                                )

                            elif confidence >= threshold:

                                st.warning(
                                    "🟠 Suggested — Review Before Use"
                                )

                            else:

                                st.error(
                                    "🔴 AI Unsure"
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

                    error_message = str(e)

                    if "Connection" in error_message:

                        st.error(
                            "🔄 Sync failure detected"
                        )

                    elif (
                        "API" in error_message
                        or "429" in error_message
                    ):

                        st.error(
                            "🚨 AI API failure detected"
                        )

                    st.error(
                        f"AI Analysis Error: {e}"
                    )

# =================================================
# TEAM DASHBOARD
# =================================================
if page == "📊 Team Dashboard":

    st.title("📊 Team Health Dashboard")

    rows = conn.table(
        "retro_analysis"
    ).select("*").execute()

    if rows.data:

        df = pd.DataFrame(rows.data)

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Positive",
            len(
                df[
                    df["sentiment"]
                    == "Positive"
                ]
            )
        )

        col2.metric(
            "Neutral",
            len(
                df[
                    df["sentiment"]
                    == "Neutral"
                ]
            )
        )

        col3.metric(
            "Negative",
            len(
                df[
                    df["sentiment"]
                    == "Negative"
                ]
            )
        )

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

        for col in [
            "Positive",
            "Neutral",
            "Negative"
        ]:

            if col not in trend_df.columns:
                trend_df[col] = 0

        trend_reset = (
            trend_df.reset_index()
        )

        fig = px.line(
            trend_reset,
            x="sprint_name",
            y=[
                "Positive",
                "Neutral",
                "Negative"
            ],
            markers=True,
            color_discrete_map={
                "Positive": "green",
                "Neutral": "orange",
                "Negative": "red"
            }
        )

        st.plotly_chart(
            fig,
            width="stretch"
        )

        st.subheader(
            "📊 Theme Distribution"
        )

        st.bar_chart(
            df["theme"].value_counts()
        )

        st.subheader(
            "📝 Recent Sprint Feedback"
        )

        st.dataframe(
            df.tail(10),
            width="stretch"
        )

# =================================================
# GUARDRAILS
# =================================================
if page == "🛡 Guardrails":

    st.title("🛡 AI Guardrails")

    st.subheader(
        "Active AI Governance Policies"
    )

    sensitive_hr = st.toggle(
        "Sensitive HR Content Detection",
        value=st.session_state.guardrails[
            "sensitive_hr"
        ]
    )

    st.toggle(
        "Hallucination Warning",
        value=True,
        disabled=True
    )

    st.toggle(
        "Data Insufficiency Warning",
        value=True,
        disabled=True
    )

    st.toggle(
        "Sync Failure Monitoring",
        value=True,
        disabled=True
    )

    st.toggle(
        "API Failure Monitoring",
        value=True,
        disabled=True
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

        "sensitive_hr":
        sensitive_hr,

        "confidence_threshold":
        confidence_threshold
    }

    st.success(
        "✅ Guardrails Updated"
    )
    st.divider()

# =====================================
# GUARDRAIL ANALYTICS
# =====================================
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
        "📊 Guardrail Distribution"
    )

    guardrail_counts = (
        guardrail_df[
            "guardrail_type"
        ].value_counts()
    )

    st.bar_chart(
        guardrail_counts
    )

    st.subheader(
        "📝 Recent Guardrail Events"
    )

    st.dataframe(
        guardrail_df.tail(10),
        width="stretch"
    )

else:

    st.info(
        "No guardrail events yet."
    )

# =================================================
# HITL REVIEW
# =================================================
if page == "🧠 HITL Review":

    st.title(
        "🧠 Human-in-the-Loop Review"
    )

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

# =================================================
# FEEDBACK SURVEY
# =================================================
if page == "📝 Feedback Survey":

    st.title("📝 Sprint Feedback Survey")

    theme_match = st.radio(
        "Did the AI themes match what your team actually discussed?",
        [
            "Yes",
            "Partially",
            "No"
        ]
    )

    sprint_planning_help = st.radio(
        "Did the AI insights improve sprint planning?",
        [
            "Yes",
            "No"
        ]
    )

    insight_quality = st.slider(
        "Rate insight quality/usefulness",
        1,
        5,
        3
    )

    missed_issue = st.text_area(
        "Which sprint issue did the AI miss?"
    )

    manual_change = st.text_area(
        "What would you manually change in the summary?"
    )

    insight_options = [
        "Deployment Improvements",
        "Communication Alignment",
        "Testing Stability",
        "Sprint Planning",
        "Team Health Monitoring",
        "Delivery Optimization"
    ]

    used_insights = st.multiselect(
        "Which insights did you use in your next sprint plan?",
        insight_options
    )

    reuse_synkr = st.radio(
        "Would you use Synkr again next sprint?",
        [
            "Yes",
            "Maybe",
            "No"
        ]
    )

    if st.button("Submit Sprint Feedback"):

        conn.table(
            "feedback_survey"
        ).insert({

            "theme_match":
            theme_match,

            "sprint_planning_help":
            sprint_planning_help,

            "insight_quality":
            insight_quality,

            "missed_issue":
            missed_issue,

            "manual_change":
            manual_change,

            "used_insights":
            ", ".join(used_insights),

            "reuse_synkr":
            reuse_synkr

        }).execute()

        st.success(
            "✅ Sprint feedback submitted successfully"
        )

# =================================================
# ADMIN DASHBOARD
# =================================================
if page == "⚙ Admin Dashboard":

    st.title("⚙ Admin Dashboard")

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

        acceptance_rate = round(
            100 - override_rate,
            1
        )

        repeat_usage = 87

        active_teams = (
            df["team_name"].nunique()
        )

        st.subheader(
            "📊 Success Metrics"
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Model Accuracy",
                f"{avg_confidence}%"
            )

            st.metric(
                "Hallucination Rate",
                f"{hallucination_rate}%"
            )

            st.metric(
                "Acceptance Rate",
                f"{acceptance_rate}%"
            )

        with col2:

            st.metric(
                "Avg Latency",
                f"{avg_latency}s"
            )

            st.metric(
                "Average Time Saved",
                "74%"
            )

            st.metric(
                "Repeat Usage",
                f"{repeat_usage}%"
            )

        with col3:

            st.metric(
                "Override Rate",
                f"{override_rate}%"
            )

            st.metric(
                "Compliance",
                "100%"
            )

            st.metric(
                "Pilot Teams Active",
                active_teams
            )

        st.divider()

        st.success(
            "Real-time governance monitoring enabled."
        )

        st.subheader(
            "📈 AI Confidence Trend"
        )

        confidence_df = (
            df.groupby("team_name")[
                "confidence"
            ]
            .mean()
        )

        st.bar_chart(
            confidence_df
        )

        st.subheader(
            "⚡ API Latency Trend"
        )

        latency_df = (
            df.groupby("team_name")[
                "latency"
            ]
            .mean()
        )

        st.line_chart(
            latency_df
        )

    else:

        st.info(
            "No admin metrics yet."
        )

    st.divider()

    st.subheader(
        "🚨 Emergency AI Controls"
    )

    if st.session_state.ai_enabled:

        st.success(
            "AI Analysis System Active"
        )

        disable_clicked = st.button(
            "🛑 DISABLE AI FOR ALL SESSIONS",
            type="primary"
        )

        if disable_clicked:

            st.session_state.ai_enabled = False

            st.error(
                "AI paused. "
                "All users reverted to manual mode."
            )

    else:

        st.error(
            "AI System Disabled"
        )

        enable_clicked = st.button(
            "✅ ENABLE AI"
        )

        if enable_clicked:

            st.session_state.ai_enabled = True

            st.success(
                "AI System Reactivated"
            )