import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pyperclip

# ----------------------------
# Gemini API Key
# ----------------------------
gemini_api_key = st.secrets.get("GEMINI_API_KEY")
model = genai.GenerativeModel("gemini-pro")

# ----------------------------
# Google Sheets setup
# ----------------------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Tour Interview Results").sheet1  # Change sheet name as needed

# ----------------------------
# Streamlit UI
# ----------------------------
st.title("🎤 Tour Interview Assistant")

interviewer = st.text_input("👤 Interviewer's Name")
name = st.text_input("🧍 Candidate's Name")
transcript = st.text_area("📝 Paste the call transcript")

if st.button("🔍 Analyze Transcript"):
    if not name or not transcript or not interviewer:
        st.warning("Please fill in all the fields.")
    else:
        prompt = f"""
        You are helping a team assess candidates for walking tour guide roles.
        Based on the transcript below, answer the following about {name}:

        1. What did you learn about {name} during the call?
        2. Should we select {name} for the tour, or assign them for a future tour? Why?
        3. Rate {name}'s potential for being a great Lokafyer on a scale of 1 to 5 and explain briefly.

        Transcript:
        {transcript}
        """

        with st.spinner("Analyzing transcript with Gemini..."):
            response = model.generate_content(prompt).text

        st.subheader("🧠 Gemini's Response:")
        st.write(response)

        # Copy to clipboard (note: only works locally with pyperclip)
        if st.button("📋 Copy to Clipboard"):
            pyperclip.copy(response)
            st.success("Copied to clipboard!")

        # Extract score (simple pattern, can be improved with regex or parsing)
        import re
        rating_match = re.search(r'(\b[1-5]\b)(?:\s*\/\s*5)?', response)
        score = rating_match.group(1) if rating_match else "N/A"

        # Save to Google Sheet
        sheet.append_row([interviewer, name, transcript, response, score])
        st.success("✅ Response saved to Google Sheets.")
