import streamlit as st
from st_supabase_connection import SupabaseConnection
from groq import Groq
import pandas as pd

# 1. Setup
conn = st.connection("supabase", type=SupabaseConnection, url=st.secrets["SUPABASE_URL"], key=st.secrets["SUPABASE_KEY"])
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.title("Synkr: Sprint Retrospective Analyzer")

# 2. THE SUMMARY SECTION (Slide 2: Team Sentiment Summary) [cite: 52]
# Fetch latest data so the summary updates immediately after a submission
rows = conn.table("retrospectives").select("*").execute()

if rows.data:
    df = pd.DataFrame(rows.data)
    st.subheader("Team Sentiment Summary") [cite: 52]
    
    # Calculate percentages for Slide 2 targets [cite: 53, 54, 55]
    counts = df['sentiment'].value_counts(normalize=True) * 100
    col1, col2, col3 = st.columns(3)
    col1.metric("Positive", f"{counts.get('Positive', 0):.0f}%") [cite: 53]
    col2.metric("Neutral", f"{counts.get('Neutral', 0):.0f}%") [cite: 54]
    col3.metric("Negative", f"{counts.get('Negative', 0):.0f}%") [cite: 55]

    # Show the "Key Themes" and "Suggested Actions" (Slide 2) [cite: 56, 61]
    st.dataframe(df[['content', 'sentiment', 'theme', 'risk_level']].tail(5)) 

st.divider()

# 3. THE INPUT BOX (Step 1: Retro Submission) [cite: 233]
# Using a form ensures the box resets and stays ready for the next "another one"
with st.form("retro_input", clear_on_submit=True):
    user_input = st.text_area("Add another retrospective comment:") [cite: 150, 234]
    submitted = st.form_submit_button("Analyze & Save")

    if submitted and user_input:
        # Step 2: AI Processing (Slide 8) [cite: 235, 236]
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{
                "role": "system", 
                "content": "Analyze sentiment (Positive/Neutral/Negative) and Theme. Return JSON."
            }, {"role": "user", "content": user_input}],
            response_format={"type": "json_object"}
        )
        
        # Parse and Save to Supabase (Slide 5 Workflow) [cite: 120, 121]
        import json
        res = json.loads(response.choices[0].message.content)
        
        conn.table("retrospectives").insert({
            "content": user_input,
            "sentiment": res.get("sentiment"),
            "theme": res.get("theme"),
            "risk_level": "Medium" # Default for prototype
        }).execute()
        
        st.success("Feedback added! The summary above has updated.")
        st.rerun() # Forces the summary at the top to refresh immediately