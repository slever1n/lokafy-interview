import streamlit as st
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
import re
import pyperclip

# ----------------------------
# API Keys and setup
# ----------------------------
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
gsheet_creds = Credentials.from_service_account_info(
    st.secrets["gsheets"], scopes=scope
)
client = gspread.authorize(gsheet_creds)
sheet = client.open("Lokafy Interview Sheet").sheet1

# ----------------------------
# Session State Defaults
# ----------------------------
for key in ["interviewer", "candidate_name", "transcript", "clear_inputs"]:
    if key not in st.session_state:
        st.session_state[key] = ""

if "clear_inputs" not in st.session_state:
    st.session_state["clear_inputs"] = False

# ----------------------------
# UI
# ----------------------------
st.title("🎤 Lokafy Interview Assistant")

# Clear Text Inputs Button
if st.button("🧹 Clear Text Inputs"):
    st.session_state["clear_inputs"] = True
    st.experimental_rerun()

# Input fields
interviewer = st.text_input("👤 Interviewer's Name", value=st.session_state.get("interviewer", ""))
candidate_name = st.text_input("🧍 Candidate's Name", value=st.session_state.get("candidate_name", ""))
transcript = st.text_area("📝 Paste the call transcript", value=st.session_state.get("transcript", ""))

# Store back to session state unless clearing
if not st.session_state["clear_inputs"]:
    st.session_state["interviewer"] = interviewer
    st.session_state["candidate_name"] = candidate_name
    st.session_state["transcript"] = transcript
else:
    st.session_state["interviewer"] = ""
    st.session_state["candidate_name"] = ""
    st.session_state["transcript"] = ""
    st.session_state["clear_inputs"] = False

# ----------------------------
# Analyze Button & Logic
# ----------------------------
if st.button("🔍 Analyze Transcript"):
    if not st.session_state["interviewer"] or not st.session_state["candidate_name"] or not st.session_state["transcript"]:
        st.warning("Please fill in all fields.")
    else:
        prompt = f"""
You're a member of a team reviewing candidates for walking tour guide roles. Based on the conversation transcript below, help us reflect on the call with {st.session_state['candidate_name']}.

Please answer these in a natural, human tone — as if you're casually writing a note to your teammate. Provide humanized answers and avoid using em-dashes.
Do not include any intros but make sure to include the questions when answering:

1. What stood out to you about {st.session_state['candidate_name']} during the call? (Mention anything interesting or memorable they shared.)
2. Do you think they’re ready to lead a tour soon, or would it be better to wait and assign them to a future one? Give a reason why.
3. What's {st.session_state['candidate_name']}'s plan for the tour? (Mention anything interesting or places that he/she has brought up during the interview)
4. Finally, on a scale of 1 to 5, how strong is their potential to be a great Lokafyer? Add a short explanation with the rating.

Here’s the transcript to base your thoughts on:
{st.session_state['transcript']}
"""

        with st.spinner("Analyzing transcript..."):
            full_response = genai.GenerativeModel("gemini-2.5-pro").generate_content(prompt).text

        st.subheader("🧠 AI Analysis")
        st.write(full_response)

        # Extract answers per question
        def extract_answer(question_number):
            pattern = rf"\*\*{question_number}\..*?\*\*\s*(.*?)(?=\n\s*\*\*|$)"
            match = re.search(pattern, full_response, re.DOTALL)
            return match.group(1).strip() if match else ""

        q1 = extract_answer("1")
        q2 = extract_answer("2")
        q3 = extract_answer("3")
        q4 = extract_answer("4")  # Full answer incl. rating and explanation

        # Save to Google Sheets (starting from column A with correct order)
        sheet.append_row([
            st.session_state["interviewer"],
            st.session_state["candidate_name"],
            st.session_state["transcript"],
            q1,
            q2,
            q3,
            q4
