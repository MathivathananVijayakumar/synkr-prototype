import streamlit as st
from st_supabase_connection import SupabaseConnection
from groq import Groq
import pandas as pd

# 1. Initialize Connections
# Force the connection to use the secrets explicitly
conn = st.connection(
    "supabase", 
    type=SupabaseConnection,
    url=st.secrets["connections"]["supabase"]["url"],
    key=st.secrets["connections"]["supabase"]["key"]
)
client = Groq(api_key=st.secrets["groq"]["api_key"])

st.title("Synkr: Team Health Dashboard")

# 2. Fetch Data from Supabase
# ttl="10m" ensures data is cached for 10 minutes to save API calls
rows = conn.query("*", table="retrospectives", ttl="10m").execute()

if rows.data:
    df = pd.DataFrame(rows.data)
    
    # 3. Display Sentiment Summary
    st.subheader("Current Sprint Sentiment")
    col1, col2, col3 = st.columns(3)
    
    # Count occurrences for the sentiment breakdown
    sentiment_counts = df['sentiment'].value_counts()
    col1.metric("Positive", f"{sentiment_counts.get('Positive', 0)}")
    col2.metric("Neutral", f"{sentiment_counts.get('Neutral', 0)}")
    col3.metric("Negative", f"{sentiment_counts.get('Negative', 0)}", delta_color="inverse")

    # 4. Actionable Insights Table
    st.subheader("Risk Alerts & Themes")
    st.dataframe(
        df[['content', 'sentiment', 'theme', 'risk_level']],
        column_config={
            "risk_level": st.column_config.TextColumn("Risk Level", help="AI-identified burnout or delivery risks")
        },
        use_container_width=True
    )

# 5. Add a New Retro Entry (Manual Input for Wizard of Oz)
with st.expander("Submit New Retrospective Feedback"):
    new_comment = st.text_area("What's on your mind?")
    if st.button("Process with Synkr AI"):
        # This calls Groq directly for real-time interaction
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": f"Analyze: {new_comment}"}],
            model="llama-3.1-8b-instant",
        )
        st.write("AI Analysis:", chat_completion.choices[0].message.content)