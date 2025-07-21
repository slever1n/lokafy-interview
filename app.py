import streamlit as st
import google.generativeai as genai
import gspread
import re
import pyperclip
from google.oauth2.service_account import Credentials

# ----------------------------
# Page Configuration
# ----------------------------
st.set_page_config(page_title="🎤 Lokafy Interview Assistant", page_icon="🎤")

# ---------- Session State Initialization ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# ---------- Helper: Authenticate User ----------
def login(username, password):
    users = st.secrets["users"]
    return username in users and users[username] == password

# ---------- Clear Refresh Param if Present ----------
if "refresh" in st.query_params:
    st.query_params.clear()

# ---------- Login Screen ----------
if not st.session_state.logged_in:
    st.set_page_config(page_title="Login | Lokafy App")
    st.title("🔐 Lokafy Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if login(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                # Add a query param to force clean rerun
                st.query_params.update(refresh="true")
                st.stop()
            else:
                st.error("Invalid username or password.")
    st.stop()

# ---------- Main App (After Login) ----------
st.set_page_config(page_title="Lokafy Dashboard")
st.title(f"👋 Welcome, {st.session_state.username}!")
st.success("You are now logged in.")

# App content goes here
st.write("✅ This is the protected part of the app.")
st.write("You can now view your dashboard, data, etc.")

# ---------- Logout ----------
if st.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.query_params.update(refresh="true")
    st.stop()

# ---------- Main App (After Login) ----------
st.set_page_config(page_title="Lokafy Dashboard")
st.title(f"👋 Welcome, {st.session_state.username}!")
st.success("You are now logged in.")

# Add your app content here
st.write("✅ This is the protected part of the app.")
st.write("You can now view your dashboard, data, etc.")

# ---------- Logout ----------
if st.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.experimental_set_query_params(refresh="true")
    st.stop()


# ---------- Main App (After Login) ----------
st.set_page_config(page_title="Lokafy Dashboard")
st.title(f"👋 Welcome, {st.session_state.username}!")
st.success("You are now logged in.")

# Add your app content here
st.write("✅ This is the protected part of the app.")
st.write("You can now view your dashboard, data, etc.")

# ---------- Logout ----------
if st.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.experimental_set_query_params(refresh="true")
    st.stop()
# ----------------------------
# App Begins After Login
# ----------------------------

# Sidebar logout
st.sidebar.success(f"Logged in as: {st.session_state.username}")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.success("Logged out.")
    st.stop()

# ----------------------------
# Gemini & Google Sheets Setup
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

col1, col2, col3 = st.columns([1, 3, 1])
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

        # Extract score from Q4
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

# ----------------------------
# Footer
# ----------------------------
st.markdown(
    "<div style='position: fixed; bottom: 10px; left: 10px; font-size: 12px; color: #c7c6c6;'>"
    "A little tool made with ❤️ by: Yul"
    "</div>", unsafe_allow_html=True)
