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

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
gsheet_creds = Credentials.from_service_account_info(
    st.secrets["gsheets"], scopes=scope
)
client = gspread.authorize(gsheet_creds)
sheet = client.open("Lokafy Interview Sheet").sheet1

def clear_all_fields():
    st.session_state.interviewer = ""
    st.session_state.candidate_name = ""
    st.session_state.transcript = ""

st.title("🎤 Lokafy Interview Assistant")

st.text_input("👤 Interviewer's Name", key="interviewer")
st.text_input("🧍 Candidate's Name", key="candidate_name")
st.text_area("📝 Paste the call transcript", key="transcript")

col1, col2 = st.columns([1, 4])  # Adjust width ratio as you like

with col1:
    st.button("🧹 Clear", on_click=clear_all_fields)

with col2:
    analyze_clicked = st.button("🔍 Analyze Transcript")

# ----------------------------
# Analyze Button & Logic
# ----------------------------
if analyze_clicked:
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
            response = genai.GenerativeModel("gemini-2.5-pro").generate_content(prompt).text

        st.subheader("🧠 AI Analysis")
        st.write(response)

        # Extract answers using regex
        q1_match = re.search(r"\*?\*?1\..*?\*?\*?\s*(.*?)(?=\*?\*?2\.)", response, re.DOTALL)
        q2_match = re.search(r"\*?\*?2\..*?\*?\*?\s*(.*?)(?=\*?\*?3\.)", response, re.DOTALL)
        q3_match = re.search(r"\*?\*?3\..*?\*?\*?\s*(.*?)(?=\*?\*?4\.)", response, re.DOTALL)
        q4_match = re.search(r"\*?\*?4\..*?\*?\*?\s*(.*)", response, re.DOTALL)

        q1 = q1_match.group(1).strip() if q1_match else ""
        q2 = q2_match.group(1).strip() if q2_match else ""
        q3 = q3_match.group(1).strip() if q3_match else ""
        q4_full = q4_match.group(1).strip() if q4_match else ""

        score_match = re.search(r"\b(?:give (?:him|her|them)|rate(?:d)?|I'd say|I’d give)\s+(?:a\s+)?([1-5])\b", response, re.IGNORECASE)
        score = score_match.group(1) if score_match else "N/A"
        explanation = q4_full.replace(score, "", 1).strip() if score != "N/A" else q4_full

        # Extract score and explanation
        score_match = re.search(r"\b([1-5])\b(?:\s*/\s*5)?", q4_full)
        score = score_match.group(1) if score_match else "N/A"
        explanation = q4_full.replace(score, "", 1).strip() if score != "N/A" else q4_full

        if st.button("📋 Copy Response to Clipboard"):
            pyperclip.copy(response)
            st.success("Response copied!")

        # Extract answers by splitting on numbered questions (1–4)
        answers = re.split(r"\*\*?\s*\d\.\s.*?\*\*?", response)

        # answers[0] is the intro or empty string; answers[1] to [4] are Q1–Q4
        q1 = answers[1].strip() if len(answers) > 1 else ""
        q2 = answers[2].strip() if len(answers) > 2 else ""
        q3 = answers[3].strip() if len(answers) > 3 else ""
        q4 = answers[4].strip() if len(answers) > 4 else ""

        # Save to Google Sheets
        sheet.append_row([
            st.session_state["interviewer"],
            st.session_state["candidate_name"],
            st.session_state["transcript"],
            q1,
            q2,
            q3,
            q4
        ])
        st.success("✅ Saved to Google Sheets!")

        # Link to the Google Sheet
        st.markdown("📄 [View Interview Sheet on Google Sheets](https://docs.google.com/spreadsheets/d/1bHODbSJmSZpl3iXPovuUDVTFrWph5xwP426OOHvWr08/edit?usp=sharing)")


st.markdown("<div style='position: fixed; bottom: 10px; left: 10px; font-size: 12px; color: #c7c6c6; '>A little tool made with ❤️ by: Yul</div>", unsafe_allow_html=True)
