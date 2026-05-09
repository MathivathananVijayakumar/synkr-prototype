import streamlit as st
from st_supabase_connection import SupabaseConnection
from groq import Groq
import pandas as pd
import json

# -----------------------------------
# PAGE CONFIG
# -----------------------------------
st.set_page_config(
    page_title="Synkr - Team Health Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Synkr: Team Health Dashboard")

# -----------------------------------
# INITIALIZE CONNECTIONS
# -----------------------------------
conn = st.connection(
    "supabase",
    type=SupabaseConnection,
    url=st.secrets["SUPABASE_URL"],
    key=st.secrets["SUPABASE_KEY"]
)

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# -----------------------------------
# LOAD EXISTING DATA
# -----------------------------------
try:
    rows = conn.table("retrospectives").select("*").execute()

    if rows.data:
        df = pd.DataFrame(rows.data)

        st.subheader("Team Sentiment Summary")

        # Sentiment percentages
        counts = df["sentiment"].value_counts(normalize=True) * 100

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Positive",
            f"{counts.get('Positive', 0):.0f}%"
        )

        col2.metric(
            "Neutral",
            f"{counts.get('Neutral', 0):.0f}%"
        )

        col3.metric(
            "Negative",
            f"{counts.get('Negative', 0):.0f}%"
        )

        st.divider()

        st.subheader("Recent Feedback")

        st.dataframe(
            df[
                ["content", "sentiment", "theme", "risk_level"]
            ].tail(10),
            use_container_width=True
        )

    else:
        st.info("No retrospective feedback found yet.")

except Exception as e:
    st.error(f"Error loading dashboard data: {e}")

st.divider()

# -----------------------------------
# INPUT FORM
# -----------------------------------
st.subheader("Submit Retro Feedback")

with st.form("retro_input", clear_on_submit=True):

    user_input = st.text_area(
        "Paste your retro feedback here...",
        height=150
    )

    submitted = st.form_submit_button("Analyze Feedback →")

    if submitted and user_input:

        try:

            # -----------------------------------
            # AI ANALYSIS USING GROQ
            # -----------------------------------
            prompt = f"""
            Analyze the following retrospective feedback.

            Return ONLY valid JSON in this format:

            {{
              "sentiment": "Positive/Neutral/Negative",
              "theme": "One short theme",
              "risk_level": "Low/Medium/High"
            }}

            Feedback:
            {user_input}
            """

            completion = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2
            )

            response_text = completion.choices[0].message.content

            # Parse AI response
            ai_response = json.loads(response_text)

            ai_sentiment = ai_response.get("sentiment", "Neutral")
            ai_theme = ai_response.get("theme", "General")
            ai_risk = ai_response.get("risk_level", "Low")

            # -----------------------------------
            # SAVE TO SUPABASE
            # -----------------------------------
            conn.table("retrospectives").insert({
                "content": user_input,
                "sentiment": ai_sentiment,
                "theme": ai_theme,
                "risk_level": ai_risk
            }).execute()

            st.success("✅ Analysis complete! Dashboard updated.")

            st.rerun()

        except Exception as e:
            st.error(f"Error analyzing feedback: {e}")