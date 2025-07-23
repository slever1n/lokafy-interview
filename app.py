import streamlit as st
import google.generativeai as genai
import gspread
import re
import pyperclip
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta

# ----------------------------
# Helper Functions
# ----------------------------
def clear_all_fields():
    st.session_state.interviewer = ""
    st.session_state.candidate_name = ""
    st.session_state.transcript = ""

def logout():
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.username_input = ""
    st.session_state.password_input = ""
    st.rerun()

# ----------------------------
# Streamlit Page Config
# ----------------------------
st.set_page_config(
    page_title="Lokafy Interview Analysis",
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

# ----------------------------
# App UI
# ----------------------------
st.title("🎤 Lokafy Interview Analysis")

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

Then, based on the rubric below, please evaluate the candidate in each category with a score from 1 to 5, and provide a brief explanation for each. Be sure to follow the scoring descriptions closely when deciding on a rating.

**Rubric Details**

1. **Communication Skills**  
1 = Struggles to articulate thoughts, unclear and difficult to understand.  
2 = Speaks hesitantly, lacks confidence, or uses minimal detail.  
3 = Communicates adequately, but lacks enthusiasm or clarity.  
4 = Speaks clearly and confidently with good engagement.  
5 = Engaging, confident, and articulate; explains concepts vividly.

2. **Local Knowledge**  
1 = Cannot name or describe local landmarks.  
2 = Names places but struggles to explain their significance.  
3 = Identifies some locations but lacks depth in explanations.  
4 = Names and describes places well with some unique insights.  
5 = Provides detailed, engaging descriptions with historical or cultural context.

3. **Enthusiasm & Engagement**  
1 = Shows no enthusiasm or interest in being a Lokafyer.  
2 = Seems unsure or unmotivated.  
3 = Interested but lacks energy or passion.  
4 = Shows excitement and genuine interest in connecting with travelers.  
5 = Highly passionate, charismatic, and eager to create a great experience.

4. **Problem-Solving Ability**  
1 = Cannot provide a solution to a traveler issue.  
2 = Struggles to handle difficult situations effectively.  
3 = Offers basic responses but lacks adaptability.  
4 = Can think quickly and offers reasonable solutions.  
5 = Handles situations creatively and proactively.

5. **Traveler Interaction**  
1 = Lacks engagement, does not personalize the experience.  
2 = Engages minimally, lacks warmth.  
3 = Tries to connect with travelers but not very dynamic.  
4 = Engages well, makes the tour feel interactive.  
5 = Exceptional ability to personalize and create an immersive experience.

6. **Bonus Score (Optional)**  
Give up to 5 bonus points for any exceptional or unique qualities (e.g. storytelling ability, adaptability, previous guide experience).

Please end with a **Total Score out of 30** (sum of the above).

Transcript:
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
        q4 = "".join(answers[4:]).strip() if len(answers) > 4 else ""

        if st.button("📋 Copy Response to Clipboard"):
            pyperclip.copy(response)
            st.success("Response copied!")

        # Extract score breakdown
        scores = re.findall(r"\*\*(.*?)\*\*:.*?(?:\bscore\b|\brating\b)?[^\d]*(\d)(?:/5)?", response, re.IGNORECASE)
        score_dict = {k.strip(): v.strip() for k, v in scores}
        total_score = sum(int(v) for v in score_dict.values() if v.isdigit())

        # Save to Google Sheets
        timestamp = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
        row = [
            timestamp,
            st.session_state["interviewer"],
            st.session_state["candidate_name"],
            st.session_state["transcript"],
            q1, q2, q3, q4,
            score_dict.get("Communication Skills", ""),
            score_dict.get("Local Knowledge", ""),
            score_dict.get("Enthusiasm & Engagement", ""),
            score_dict.get("Problem-Solving Ability", ""),
            score_dict.get("Traveler Interaction", ""),
            score_dict.get("Bonus Score", ""),
            total_score
        ]
        sheet.append_row(row)
        st.success("✅ Saved to Google Sheets!")

        st.markdown("📄 [View Interview Sheet on Google Sheets](https://docs.google.com/spreadsheets/d/1bHODbSJmSZpl3iXPovuUDVTFrWph5xwP426OOHvWr08/edit?usp=sharing)")

if st.button("❌ Logout"):
    logout()

st.markdown("<div style='position: fixed; bottom: 10px; left: 10px; font-size: 12px; color: #c7c6c6;'>A little tool made with ❤️ by: Yul</div>", unsafe_allow_html=True)
