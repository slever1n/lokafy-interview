import streamlit as st
import google.generativeai as genai
import gspread
import re
import pyperclip
from google.oauth2.service_account import Credentials

# ----------------------------
# API Keys from .streamlit/secrets.toml
# ----------------------------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Google Sheets authentication
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
gsheet_creds = Credentials.from_service_account_info(st.secrets["gsheets"], scopes=scope)
client = gspread.authorize(gsheet_creds)
spreadsheet_list = client.openall()
st.write([s.title for s in spreadsheet_list])
sheet = client.open("Lokafy Interview Sheet").sheet1  # Your sheet name here

# ----------------------------
# Streamlit UI
# ----------------------------
st.title("🎤 Lokafy Interview Assistant")

interviewer = st.text_input("👤 Interviewer's Name")
candidate_name = st.text_input("🧍 Candidate's Name")
transcript = st.text_area("📝 Paste the call transcript")

if st.button("🔍 Analyze Transcript"):
    if not interviewer or not candidate_name or not transcript:
        st.warning("Please fill in all fields.")
    else:
        prompt = f"""
        You are helping a team assess candidates for walking tour guide roles.
        Based on the transcript below, answer the following about {candidate_name}:

        1. What did you learn about {candidate_name} during the call?
        2. Should we select {candidate_name} for the tour, or assign them for a future tour? Why?
        3. Rate {candidate_name}'s potential for being a great Lokafyer on a scale of 1 to 5 and explain briefly.

        Transcript:
        {transcript}
        """

        with st.spinner("Analyzing transcript with Gemini..."):
            response = genai.GenerativeModel("gemini-pro").generate_content(prompt).text

        st.subheader("🧠 Gemini's Response")
        st.write(response)

        # Extract rating from response
        rating_match = re.search(r"\b([1-5])\b(?:\s*/\s*5)?", response)
        score = rating_match.group(1) if rating_match else "N/A"

        # Copy to clipboard button
        if st.button("📋 Copy Response to Clipboard"):
            pyperclip.copy(response)
            st.success("Response copied!")

        # Save to Google Sheets
        sheet.append_row([interviewer, candidate_name, transcript, response, score])
        st.success("✅ Saved to Google Sheets!")
