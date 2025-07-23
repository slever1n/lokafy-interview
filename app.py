import streamlit as st
import google.generativeai as genai
import gspread
import re
import pyperclip
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta
import re

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

**Q1.** What did we learn about {st.session_state['candidate_name']} during the call? (Mention anything interesting or memorable they shared.)
**Q2.** Do you think they're ready to lead a tour soon, or would it be better to wait and assign them to a future one? Give a reason why.
**Q3.** What's {st.session_state['candidate_name']}'s plan for the tour? (Mention anything interesting or places that he/she has brought up during the interview)

4. Then, based on the rubric below, please evaluate the candidate in each category with a score from 1 to 5, and provide a brief explanation for each. Be sure to follow the scoring descriptions closely when deciding on a rating.

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
        Give up to 5 bonus points for answers if the candidate:
            - Shared a unique, lesser-known fact about the city (+1)
            - Gave an exceptional storytelling example during the mock tour(+1)
            - Demonstrated strong adaptability (e.g., handled a difficult traveler scenario well)(+1)
            - Showed genuine passion for connecting with travelers(+1)
            - Suggested a creative or unique way to enhance traveler experience(+1)

    Please end with a **Total Score out of 30** (sum of the above).

        Format your responses this way:
        **Communication Skills**  
        Score: X/5  
        Explanation: ...

        **Local Knowledge**  
        Score: X/5  
        Explanation: ...

        **Enthusiasm & Engagement**  
        Score: X/5  
        Explanation: ...

        **Problem-Solving Ability**  
        Score: X/5  
        Explanation: ...

        **Traveler Interaction**  
        Score: X/5  
        Explanation: ...

        **Bonus Score**  
        Score: X/5  
        Explanation: ...

        End with a line that says:  
        **Total Score out of 30:** 

Transcript:
{st.session_state['transcript']}
"""

        with st.spinner("Analyzing transcript..."):
            response = genai.GenerativeModel("gemini-2.5-pro").generate_content(prompt).text

        st.subheader("🧠 AI Analysis")
        st.write(response)


        def extract_section(start_marker, next_marker, text):
            pattern = rf"{re.escape(start_marker)}\s*(.*?)(?=\n\s*{re.escape(next_marker)}|\Z)"
            match = re.search(pattern, text, re.DOTALL)
            return match.group(1).strip() if match else ""

        # Define question texts using the candidate's name from session
        q1_text = "**Q1."
        q2_text = "**Q2."
        q3_text = "**Q3."
        rubric_markers = [
            "**Rubric Evaluation**",
            "**Communication Skills**", 
            "**Q4.**", 
            "**Evaluation**"
        ]
        rubric_marker = next((m for m in rubric_markers if m in response), "**Communication Skills**")

        # Extract answers
        q1 = extract_section(q1_text, q2_text, response)
        q2 = extract_section(q2_text, q3_text, response)
        q3 = extract_section(q3_text, rubric_marker, response)

        # Q4 = everything from the rubric section onward
        q4_start = response.find(rubric_marker)
        q4 = response[q4_start:].strip() if q4_start != -1 else ""


        rubric_keys = [
            "Communication Skills",
            "Local Knowledge",
            "Enthusiasm & Engagement",
            "Problem-Solving Ability",
            "Traveler Interaction",
            "Bonus Score"
        ]

        score_dict = {}
        explanation_dict = {}

        for key in rubric_keys:
            pattern = rf"\*\*{re.escape(key)}\*\*\s*Score:\s*(\d)(?:/5)?\s*Explanation:\s*(.*?)(?=\n\*\*|\n*$)"
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                score_dict[key] = match.group(1).strip()
                explanation_dict[key] = match.group(2).strip()
            else:
                score_dict[key] = ""
                explanation_dict[key] = ""

        total_score = sum(int(v) for v in score_dict.values() if v.isdigit())

        timestamp = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
        row = [
            timestamp,
            st.session_state["interviewer"],
            st.session_state["candidate_name"],
            st.session_state["transcript"],
            q1,
            q2,
            q3,
            q4,
            score_dict.get("Communication Skills", ""),
            explanation_dict.get("Communication Skills", ""),
            score_dict.get("Local Knowledge", ""),
            explanation_dict.get("Local Knowledge", ""),
            score_dict.get("Enthusiasm & Engagement", ""),
            explanation_dict.get("Enthusiasm & Engagement", ""),
            score_dict.get("Problem-Solving Ability", ""),
            explanation_dict.get("Problem-Solving Ability", ""),
            score_dict.get("Traveler Interaction", ""),
            explanation_dict.get("Traveler Interaction", ""),
            score_dict.get("Bonus Score", ""),
            explanation_dict.get("Bonus Score", ""),
            total_score
        ]

        sheet.append_row(row)
        st.success("✅ Saved to Google Sheets!")

        st.markdown("📄 [View Interview Sheet on Google Sheets](https://docs.google.com/spreadsheets/d/1bHODbSJmSZpl3iXPovuUDVTFrWph5xwP426OOHvWr08/edit?usp=sharing)")

if st.button("❌ Logout"):
    logout()

st.markdown("<div style='position: fixed; bottom: 10px; left: 10px; font-size: 12px; color: #c7c6c6;'>A little tool made with ❤️ by: Yul</div>", unsafe_allow_html=True)
import streamlit as st
import google.generativeai as genai
import gspread
import re
import pyperclip
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta
import re

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

**Q1.** What did we learn about {st.session_state['candidate_name']} during the call? (Mention anything interesting or memorable they shared.)
**Q2.** Do you think they're ready to lead a tour soon, or would it be better to wait and assign them to a future one? Give a reason why.
**Q3.** What's {st.session_state['candidate_name']}'s plan for the tour? (Mention anything interesting or places that he/she has brought up during the interview)

4. Then, based on the rubric below, please evaluate the candidate in each category with a score from 1 to 5, and provide a brief explanation for each. Be sure to follow the scoring descriptions closely when deciding on a rating.

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
        Give up to 5 bonus points for answers if the candidate:
            - Shared a unique, lesser-known fact about the city (+1)
            - Gave an exceptional storytelling example during the mock tour(+1)
            - Demonstrated strong adaptability (e.g., handled a difficult traveler scenario well)(+1)
            - Showed genuine passion for connecting with travelers(+1)
            - Suggested a creative or unique way to enhance traveler experience(+1)

    Please end with a **Total Score out of 30** (sum of the above).

        Format your responses this way:
        **Communication Skills**  
        Score: X/5  
        Explanation: ...

        **Local Knowledge**  
        Score: X/5  
        Explanation: ...

        **Enthusiasm & Engagement**  
        Score: X/5  
        Explanation: ...

        **Problem-Solving Ability**  
        Score: X/5  
        Explanation: ...

        **Traveler Interaction**  
        Score: X/5  
        Explanation: ...

        **Bonus Score**  
        Score: X/5  
        Explanation: ...

        End with a line that says:  
        **Total Score out of 30:** 

Transcript:
{st.session_state['transcript']}
"""

        with st.spinner("Analyzing transcript..."):
            response = genai.GenerativeModel("gemini-2.5-pro").generate_content(prompt).text

        st.subheader("🧠 AI Analysis")
        st.write(response)


        def extract_section(start_marker, next_marker, text):
            pattern = rf"{re.escape(start_marker)}(.*?)(?={re.escape(next_marker)}|\Z)"
            match = re.search(pattern, text, re.DOTALL)
            return match.group(1).strip() if match else ""

        # Define the marker for the start of Q4
        rubric_marker = "**Rubric Evaluation**"

        # Define question texts using the candidate's name from session
        q1_text = "**Q1."
        q2_text = "**Q2."
        q3_text = "**Q3."
        rubric_marker = "**Communication Skills"


        # Extract answers
        q1 = extract_section(q1_text, q2_text, response)
        q2 = extract_section(q2_text, q3_text, response)
        q3 = extract_section(q3_text, rubric_marker, response)

        # Q4 = everything from the rubric section onward
        q4_start = response.find(rubric_marker)
        q4 = response[q4_start:].strip() if q4_start != -1 else ""


        rubric_keys = [
            "Communication Skills",
            "Local Knowledge",
            "Enthusiasm & Engagement",
            "Problem-Solving Ability",
            "Traveler Interaction",
            "Bonus Score"
        ]

        score_dict = {}
        explanation_dict = {}

        for key in rubric_keys:
            pattern = rf"\*\*{re.escape(key)}\*\*\s*Score:\s*(\d)(?:/5)?\s*Explanation:\s*(.*?)(?=\n\*\*|\n*$)"
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                score_dict[key] = match.group(1).strip()
                explanation_dict[key] = match.group(2).strip()
            else:
                score_dict[key] = ""
                explanation_dict[key] = ""

        total_score = sum(int(v) for v in score_dict.values() if v.isdigit())

        timestamp = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
        row = [
            timestamp,
            st.session_state["interviewer"],
            st.session_state["candidate_name"],
            st.session_state["transcript"],
            q1,
            q2,
            q3,
            q4,
            score_dict.get("Communication Skills", ""),
            explanation_dict.get("Communication Skills", ""),
            score_dict.get("Local Knowledge", ""),
            explanation_dict.get("Local Knowledge", ""),
            score_dict.get("Enthusiasm & Engagement", ""),
            explanation_dict.get("Enthusiasm & Engagement", ""),
            score_dict.get("Problem-Solving Ability", ""),
            explanation_dict.get("Problem-Solving Ability", ""),
            score_dict.get("Traveler Interaction", ""),
            explanation_dict.get("Traveler Interaction", ""),
            score_dict.get("Bonus Score", ""),
            explanation_dict.get("Bonus Score", ""),
            total_score
        ]

        sheet.append_row(row)
        st.success("✅ Saved to Google Sheets!")

        st.markdown("📄 [View Interview Sheet on Google Sheets](https://docs.google.com/spreadsheets/d/1bHODbSJmSZpl3iXPovuUDVTFrWph5xwP426OOHvWr08/edit?usp=sharing)")

if st.button("❌ Logout"):
    logout()

st.markdown("<div style='position: fixed; bottom: 10px; left: 10px; font-size: 12px; color: #c7c6c6;'>A little tool made with ❤️ by: Yul</div>", unsafe_allow_html=True)
