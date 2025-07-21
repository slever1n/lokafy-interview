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
for key in ["interviewer", "candidate_name", "transcript", "should_rerun"]:
    if key not in st.session_state:
        st.session_state[key] = ""

# ----------------------------
# UI
# ----------------------------
st.title("🎤 Lokafy Interview Assistant")

st.session_state["interviewer"] = st.text_input("👤 Interviewer's Name", value=st.session_state.get("interviewer", ""))
st.session_state["candidate_name"] = st.text_input("🧍 Candidate's Name", value=st.session_state.get("candidate_name", ""))
st.session_state["transcript"] = st.text_area("📝 Paste the call transcript", value=st.session_state.get("transcript", ""))

# Clear button
if st.button("🧹 Clear All Fields"):
    st.session_state["interviewer"] = ""
    st.session_state["candidate_name"] = ""
    st.session_state["transcript"] = ""
    st.session_state["should_rerun"] = True

# Analyze
if st.button("🔍 Analyze Transcript"):
    if not st.session_state["interviewer"] or not st.session_state["candidate_name"] or not st.session_state["transcript"]:
        st.warning("Please fill in all fields.")
    else:
        prompt = f"""
        You are helping a team assess candidates for walking tour guide roles.
        Based on the transcript below, answer the following about {st.session_state['candidate_name']}:

        1. What did you learn about {st.session_state['candidate_name']} during the call?
        2. Should we select {st.session_state['candidate_name']} for the tour, or assign them for a future tour? Why?
        3. Rate {st.session_state['candidate_name']}'s potential for being a great Lokafyer on a scale of 1 to 5 and explain briefly.

        Transcript:
        {st.session_state['transcript']}
        """

        with st.spinner("Analyzing transcript with Gemini..."):
            response = genai.GenerativeModel("gemini-2.5-pro").generate_content(prompt).text

        st.subheader("🧠 Gemini's Response")
        st.write(response)

        rating_match = re.search(r"\b([1-5])\b(?:\s*/\s*5)?", response)
        score = rating_match.group(1) if rating_match else "N/A"

        if st.button("📋 Copy Response to Clipboard"):
            pyperclip.copy(response)
            st.success("Response copied!")

        sheet.append_row([
            st.session_state["interviewer"],
            st.session_state["candidate_name"],
            st.session_state["transcript"],
            response,
            score
        ])
        st.success("✅ Saved to Google Sheets!")
        st.markdown("📄 [View Interview Sheet on Google Sheets](https://docs.google.com/spreadsheets/d/1bHODbSJmSZpl3iXPovuUDVTFrWph5xwP426OOHvWr08/edit?usp=sharing)")


# Handle rerun flag AFTER all Streamlit widgets have rendered
if st.session_state.get("should_rerun"):
    st.session_state["should_rerun"] = False
    st.experimental_rerun()
