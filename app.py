import streamlit as st
import google.generativeai as genai
import gspread
import re
import pyperclip
from google.oauth2.service_account import Credentials


st.set_page_config(
    page_title="Lokafy Interview Assistant",
    page_icon="🎤",
    layout="centered",
)

# ----------------------------
# Login Handling
# ----------------------------



if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_login():
    users = st.secrets["users"]
    username = st.session_state.get("username_input")
    password = st.session_state.get("password_input")
    if username in users and users[username] == password:
        st.session_state.authenticated = True

    else:
        st.error("Invalid username or password")

if not st.session_state.authenticated:
    st.title("🔐 Login")
    st.text_input("Username", key="username_input")
    st.text_input("Password", type="password", key="password_input")
    st.button("Login", on_click=check_login)
    st.stop()



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

# ----------------------------
# App UI
# ----------------------------
st.title("🎤 Lokafy Interview Assistant")

st.text_input("👤 Interviewer's Name", key="interviewer")
st.text_input("🧍 Lokafyer's Name", key="candidate_name")
st.text_area("📝 Paste the call transcript", key="transcript")

col1, col2, col3 = st.columns([1, 4, 1])

with col1:
    st.button("🧹 Clear", on_click=clear_all_fields)

with col3:
    analyze_clicked = st.button("🔍 Analyze")

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

        # Extract answers
        answers = re.split(r"\*\*?\s*\d\.\s.*?\*\*?", response)

        q1 = answers[1].strip() if len(answers) > 1 else ""
        q2 = answers[2].strip() if len(answers) > 2 else ""
        q3 = answers[3].strip() if len(answers) > 3 else ""
        q4 = answers[4].strip() if len(answers) > 4 else ""

        score_match = re.search(r"\b([1-5])\b(?:\s*/\s*5)?", q4)
        score = score_match.group(1) if score_match else "N/A"
        explanation = q4.replace(score, "", 1).strip() if score != "N/A" else q4

        if st.button("📋 Copy Response to Clipboard"):
            pyperclip.copy(response)
            st.success("Response copied!")

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

        st.markdown("📄 [View Interview Sheet on Google Sheets](https://docs.google.com/spreadsheets/d/1bHODbSJmSZpl3iXPovuUDVTFrWph5xwP426OOHvWr08/edit?usp=sharing)")


def logout():
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.username_input = ""
    st.session_state.password_input = ""
    st.rerun()

if st.button("Logout"):
        logout()

st.markdown("<div style='position: fixed; bottom: 10px; left: 10px; font-size: 12px; color: #c7c6c6;'>A little tool made with ❤️ by: Yul</div>", unsafe_allow_html=True)
