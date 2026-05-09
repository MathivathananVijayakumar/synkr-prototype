import streamlit as st
from st_supabase_connection import SupabaseConnection
from groq import Groq
import pandas as pd
import json

# 1. Initialize Connections
conn = st.connection(
    "supabase", 
    type=SupabaseConnection,
    url=st.secrets["SUPABASE_URL"],
    key=st.secrets["SUPABASE_KEY"]
)
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.title("Synkr: Team Health Dashboard")

# 2. THE SUMMARY SECTION (Slide 2: Team Sentiment Summary)
# This displays the dashboard metrics first [cite: 241, 242]
rows = conn.table("retrospectives").select("*").execute()

if rows.data:
    df = pd.DataFrame(rows.data)
    st.subheader("Team Sentiment Summary")
    
    # Calculate percentages for the summary [cite: 52, 53, 54, 55]
    counts = df['sentiment'].value_counts(normalize=True) * 100
    col1, col2, col3 = st.columns(3)
    col1.metric("Positive", f"{counts.get('Positive', 0):.0f}%")
    col2.metric("Neutral", f"{counts.get('Neutral', 0):.0f}%")
    col3.metric("Negative", f"{counts.get('Negative', 0):.0f}%")

    # Display the risk signals and themes [cite: 56, 148]
    st.dataframe(df[['content', 'sentiment', 'theme', 'risk_level']].tail(10)) 

st.divider()

# 3. THE INPUT BOX (Slide 8: Step 1 - Retro Submission)
# Form resets after submit, keeping the dashboard ready for "another one" 
with st.form("retro_input", clear_on_submit=True):
    user_input = st.text_area("Paste your retro feedback here...") [cite: 414]
    submitted = st.form_submit_button("Analyze Feedback →") [cite: 416]

    if submitted and user_input:
        # 1. AI Processing (Groq) logic goes here...
        
        # 2. Insert into Supabase
        conn.table("retrospectives").insert({
            "content": user_input,
            "sentiment": ai_sentiment,
            "theme": ai_theme,
            "risk_level": ai_risk
        }).execute()
        
        # 3. THE FIX: Update here
        st.success("Analysis complete! Updating dashboard...")
        st.rerun()  # This triggers the refresh to show the new metrics [cite: 469]