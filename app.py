import streamlit as st
import google.generativeai as genai
import gspread
import re
import pyperclip
from google.oauth2.service_account import Credentials

# ----------------------------
# API Keys and setup
# ----------------------------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
gsheet_creds = Credentials.from_service_account_info(st.secrets["gsheets"], scopes=scope)
client = gspread.authorize(gsheet_creds)
sheet = client.open("Lokafy Interview Sheet").sheet1

# ----------------------------
# Session State Defaults
# ----------------------------
for key in ["interviewer", "candidate_name", "transcript"]:
    if key not in st.session_state:
        st.session_state[key] = ""

# ----------------------------
# UI
# ----------------------------
st.title("🎤 Lokafy Interview Assistant")

# Input fields
st.session_state["interviewer"] = st.text_input("👤 Interviewer's Name", value=st.session_state["interviewer"])
st.session_state["candidate_name"] = st.text_input("🧍 Candidate's Name", value=st.session_state["candidate_name"])
st.session_state["transcript"] = st.text_area("📝 Paste the call transcript", value=st.session_state["transcript"])

# Analyze
if st.button("🔍 Analyze Transcript"):
    if not st.session_state["interviewer"] or not st.session_state["candidate_name"] or not st.session_state["transcript"]:
        st.warning("Please fill in all fields.")
    else:
prompt = f"""
    You're a member of a team reviewing candidates for walking tour guide roles. Based on the conversation transcript below, help us reflect on the call with {st.session_state['candidate_name']}.

    Please answer these in a natural, human tone — as if you're casually writing a note to your teammate:
    
    1. What stood out to you about {st.session_state['candidate_name']} during the call? (Mention anything interesting or memorable they shared.)
    2. Do you think they’re ready to lead a tour soon, or would it be better to wait and assign them to a future one? Give a quick reason why.
    3. Finally, on a scale of 1 to 5, how strong is their potential to be a great Lokafyer? Add a short explanation with the rating.

    Here’s the transcript to base your thoughts on:
    {st.session_state['transcript']}
"""

        with st.spinner("Analyzing transcript..."):
            response = genai.GenerativeModel("gemini-2.5-pro").generate_content(prompt).text

        st.subheader("🧠 AI Analysis")
        st.write(response)

        rating_match = re.search(r"\b([1-5])\b(?:\s*/\s*5)?", response)
        score = rating_match.group(1) if rating_match else "N/A"

        if st.button("📋 Copy Response to Clipboard"):
            pyperclip.copy(response)
            st.success("Response copied!")

        # Save to sheet
        sheet.append_row([
            st.session_state["interviewer"],
            st.session_state["candidate_name"],
            st.session_state["transcript"],
            response,
            score
        ])
        st.success("✅ Saved to Google Sheets!")

        # Link to the sheet
        st.markdown("📄 [View Interview Sheet on Google Sheets](https://docs.google.com/spreadsheets/d/1bHODbSJmSZpl3iXPovuUDVTFrWph5xwP426OOHvWr08/edit?usp=sharing)")
