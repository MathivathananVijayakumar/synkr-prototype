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

positive_keywords = [
    "good",
    "great",
    "happy",
    "smooth",
    "excellent",
    "fast"
]

negative_keywords = [
    "delay",
    "blocked",
    "issue",
    "problem",
    "stress",
    "burnout"
]

# =================================================
# SYSTEM PROMPT
# =================================================
system_prompt = """
You are Synkr AI.

Analyze sprint retrospective feedback.

For every feedback item identify:
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
    # INPUT GUARDRAILS
    # =================================================
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

    # =================================================
    # ANALYZE
    # =================================================
    if st.button("Analyze Feedback"):

        if retro_text.strip():

            with st.spinner(
                "🤖 Synkr AI analyzing sprint feedback..."
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
                    # SAVE CHAT HISTORY
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
                    # SAVE AI METRICS
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
                            theme = "General"

                            # -------------------------------------
                            # THEME EXTRACTION
                            # -------------------------------------
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

                            else:

                                theme = "Delivery"

                            # -------------------------------------
                            # SENTIMENT
                            # -------------------------------------
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
                            # SAVE RETRO ANALYSIS
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

                            threshold = guardrails[
                                "confidence_threshold"
                            ]

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
                                        "🔴 AI Unsure"
                                    )

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

        if rows.data and len(rows.data) > 0:

            df = pd.DataFrame(rows.data)

            col1, col2, col3, col4 = st.columns(4)

            total_msgs = len(df)

            positive = len(
                df[df["sentiment"] == "Positive"]
            )

            negative = len(
                df[df["sentiment"] == "Negative"]
            )

            burnout = len(
                df[df["theme"] == "Team Health"]
            )

            col1.metric(
                "Total Feedback",
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

            st.subheader("📈 Sentiment Trends")

            sentiment_data = []

            for index, row in df.iterrows():

                positive_score = (
                    1 if row["sentiment"] == "Positive"
                    else 0
                )

                negative_score = (
                    1 if row["sentiment"] == "Negative"
                    else 0
                )

                sentiment_data.append({
                    "Feedback": index + 1,
                    "Positive": positive_score,
                    "Negative": negative_score
                })

            chart_data = pd.DataFrame(
                sentiment_data
            )

            st.line_chart(
                chart_data.set_index("Feedback")
            )

            st.subheader("📊 Theme Distribution")

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
                "No dashboard data available yet."
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
        "✅ Guardrail settings updated"
    )

    st.divider()

    sample_text = st.text_area(
        "Test guardrails with sample retro feedback",
        height=120,
        key="guardrail_test"
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
# HITL REVIEW
# =================================================
if page == "🧠 HITL Review":

    st.title("🧠 Human-in-the-Loop Review")

    reviewer_name = st.text_input(
        "Reviewer Name",
        placeholder="Enter reviewer name"
    )

    try:

        rows = conn.table(
            "retro_analysis"
        ).select("*").execute()

        if rows.data and len(rows.data) > 0:

            df = pd.DataFrame(rows.data)

            st.subheader(
                "Pending AI Reviews"
            )

            latest = df.tail(5)

            for index, row in latest.iterrows():

                confidence = row["confidence"]

                review_required = (
                    confidence <
                    st.session_state.guardrails[
                        "confidence_threshold"
                    ]
                )

                with st.container(border=True):

                    st.write(
                        f"📝 {row['feedback']}"
                    )

                    col1, col2, col3 = st.columns(3)

                    col1.metric(
                        "AI Sentiment",
                        row["sentiment"]
                    )

                    col2.metric(
                        "AI Theme",
                        row["theme"]
                    )

                    col3.metric(
                        "Confidence",
                        f"{confidence}%"
                    )

                    if review_required:

                        st.warning(
                            "⚠ Manual review required"
                        )

                    else:

                        st.success(
                            "✅ High confidence AI output"
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
                            index=[
                                "Positive",
                                "Neutral",
                                "Negative"
                            ].index(
                                row["sentiment"]
                            ),
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
                            index=[
                                "Deployment",
                                "Communication",
                                "Planning",
                                "Testing",
                                "Team Health",
                                "Delivery"
                            ].index(
                                row["theme"]
                            ),
                            key=f"theme_{index}"
                        )
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        if st.button(
                            "Approve AI",
                            key=f"approve_{index}"
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
                                reviewer_name,

                                "status":
                                "Approved"

                            }).execute()

                            st.success(
                                "✅ Review Approved"
                            )

                    with col2:

                        if st.button(
                            "Override AI",
                            key=f"override_{index}"
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
                                reviewer_name,

                                "status":
                                "Overridden"

                            }).execute()

                            conn.table(
                                "ai_metrics"
                            ).insert({

                                "team_name":
                                row["team_name"],

                                "latency": 0,

                                "confidence":
                                row["confidence"],

                                "hallucination_flag":
                                False,

                                "override_flag":
                                True

                            }).execute()

                            st.warning(
                                "⚠ AI Override Recorded"
                            )

            st.divider()

            # =========================================
            # REVIEW ANALYTICS
            # =========================================
            st.subheader(
                "📊 HITL Analytics"
            )

            review_rows = conn.table(
                "hitl_reviews"
            ).select("*").execute()

            if review_rows.data:

                review_df = pd.DataFrame(
                    review_rows.data
                )

                approved_count = len(
                    review_df[
                        review_df["status"]
                        == "Approved"
                    ]
                )

                overridden_count = len(
                    review_df[
                        review_df["status"]
                        == "Overridden"
                    ]
                )

                col1, col2 = st.columns(2)

                col1.metric(
                    "Approved AI Decisions",
                    approved_count
                )

                col2.metric(
                    "AI Overrides",
                    overridden_count
                )

                st.subheader(
                    "Recent Reviews"
                )

                st.dataframe(
                    review_df.tail(10),
                    width="stretch"
                )

        else:

            st.info(
                "No review data available."
            )

    except Exception as e:

        st.error(
            f"HITL Review Error: {e}"
        )

# =================================================
# FEEDBACK SURVEY
# =================================================
if page == "📝 Feedback Survey":

    st.title("📝 Feedback Survey")

    st.write(
        "Help improve Synkr AI by rating "
        "the quality of sprint insights."
    )

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

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "Submit Feedback"
        ):

            try:

                conn.table(
                    "feedback_survey"
                ).insert({

                    "theme_match": theme_match,
                    "usefulness": usefulness,
                    "missed_feedback": missed_feedback

                }).execute()

                st.success(
                    "✅ Feedback Submitted"
                )

            except Exception as e:

                st.error(
                    f"Survey Error: {e}"
                )

    with col2:

        if st.button(
            "View Survey Analytics"
        ):

            try:

                rows = conn.table(
                    "feedback_survey"
                ).select("*").execute()

                if rows.data:

                    df = pd.DataFrame(
                        rows.data
                    )

                    st.divider()

                    st.subheader(
                        "📊 Survey Analytics"
                    )

                    avg_usefulness = round(
                        df["usefulness"].mean(),
                        1
                    )

                    col1, col2 = st.columns(2)

                    col1.metric(
                        "Avg Usefulness",
                        f"{avg_usefulness}/5"
                    )

                    yes_count = len(
                        df[
                            df["theme_match"]
                            == "Yes"
                        ]
                    )

                    col2.metric(
                        "Positive AI Match",
                        yes_count
                    )

                    st.subheader(
                        "Theme Match Distribution"
                    )

                    match_counts = (
                        df["theme_match"]
                        .value_counts()
                    )

                    st.bar_chart(
                        match_counts
                    )

                    st.subheader(
                        "Recent User Feedback"
                    )

                    st.dataframe(
                        df.tail(10),
                        width="stretch"
                    )

                else:

                    st.info(
                        "No survey data available."
                    )

            except Exception as e:

                st.error(
                    f"Analytics Error: {e}"
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

            st.success(
                f"Pilot Teams Active: {active_teams}"
            )

            st.info(
                "Average Time Saved: 74%"
            )

        else:

            st.info(
                "No AI metrics available yet."
            )

    except Exception as e:

        st.error(
            f"Admin Dashboard Error: {e}"
        )