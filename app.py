# python naukri_launcher_automated_code.py
# python button_click.py
# python -m streamlit run app.py
# python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501
# http://192.168.161:8501

import streamlit as st
import requests
import time
import os
import pandas as pd
import gspread
import re
import shutil
import json
import zipfile
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.service_account import Credentials
import pygetwindow as gw
from flask import Flask
import threading

SETTINGS_FILE = "settings.json"
RESUME_DIR = r"C:\Users\Admin\naukri_automation\resumes"
SHORTLISTED_DIR = r"C:\Users\Admin\naukri_automation\shortlisted&rejected"

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {"rej_months": 6, "rej_days": 0}  # default
    with open(SETTINGS_FILE, "r") as f:
        return json.load(f)

def save_settings(data):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f)

def get_uid(url):
    try:
        if "uniqId=" in url:
            uniq = url.split("uniqId=")[1]
            uniq = uniq[:32 + 36]
            return uniq[32:32+36]
        
        return url
    except:
        return url

def remove_shortlisted(selected_df):

    all_data = sheet1.get_all_records()

    if not all_data:
        return

    df = pd.DataFrame(all_data)

    # extract unique IDs
    df["UID"] = df["ProfileURL"].apply(get_uid)

    selected_df = selected_df.copy()
    selected_df["UID"] = selected_df["ProfileURL"].apply(get_uid)

    selected_uids = set(selected_df["UID"])

    # remove matching rows
    df = df[~df["UID"].isin(selected_uids)]

    # drop helper column
    df = df.drop(columns=["UID"])

    # store headers BEFORE clearing
    headers = df.columns.tolist()

    # rewrite sheet
    sheet1.clear()

    # ALWAYS write header
    sheet1.append_row(headers)

    # write data only if exists
    if not df.empty:
        sheet1.append_rows(df.values.tolist())

# =========================
# EMAIL FUNCTION
# =========================
def send_email(email_dt, User_Name):

    from_add = '---' # email
    from_add_pass = 'vmad orko wzgj ytzk'

    to_add = ['rishithmangatt@gmail.com']
    to_cc = []

    subject = f'Email Subject {email_dt}'

    content = f'''
    <html>
        <body>
            <p><b>Dear {User_Name},</b></p>
            <p>Body of the email.</p>
            <p>Regards,</p>
        </body>
    </html>
    '''

    msg = MIMEMultipart()
    msg['From'] = from_add
    msg['To'] = ','.join(to_add)
    msg['Cc'] = ','.join(to_cc)
    msg['Subject'] = subject

    msg.attach(MIMEText(content, 'html'))

    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(from_add, from_add_pass)
    s.send_message(msg, from_add, to_add + to_cc)
    s.quit()


# =========================
# CONFIG
# =========================
WEBHOOK_URL = "http://localhost:5678/webhook/state"

SERVICE_ACCOUNT_FILE = r"C:\Users\Admin\naukri_automation\soch-496111-1c5abfdf4dae.json"

SPREADSHEET_NAME = "Naukri Candidates"
SHEET1_NAME = "Sheet1"
SHEET2_NAME = "Sheet2"
SHEET3_NAME = "Sheet3"
SHEET4_NAME = "Sheet4"

# =========================
# GOOGLE SHEETS SETUP
# =========================
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_sheets():
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )

    client = gspread.authorize(creds)
    spreadsheet = client.open(SPREADSHEET_NAME)

    sheet1 = spreadsheet.worksheet(SHEET1_NAME)
    sheet2 = spreadsheet.worksheet(SHEET2_NAME)
    sheet3 = spreadsheet.worksheet(SHEET3_NAME)
    sheet4 = spreadsheet.worksheet(SHEET4_NAME)

    return sheet1, sheet2, sheet3, sheet4


sheet1, sheet2, sheet3, sheet4 = get_sheets()

# =========================
# FLASK ERROR LISTENER
# =========================

flask_app = Flask(__name__)

if "google_sheet_error" not in st.session_state:
    st.session_state.google_sheet_error = False

@flask_app.route("/google_sheet_error", methods=["POST"])
def google_sheet_error():
    st.session_state.google_sheet_error = True
    return {"status": "received"}, 200

def run_flask():
    flask_app.run(
        host="0.0.0.0",
        port=5002,
        debug=False,
        use_reloader=False
    )

# START FLASK ONLY ONCE
if "flask_started" not in st.session_state:
    threading.Thread(target=run_flask, daemon=True).start()
    st.session_state.flask_started = True

@st.cache_data(ttl=10)
def get_sheet3_data():
    return pd.DataFrame(sheet3.get_all_records())

@st.cache_data(ttl=10)
def get_sheet4_data():
    return pd.DataFrame(sheet4.get_all_records())

# =========================
# SESSION STATE
# =========================
if "clear_trigger" not in st.session_state:
    st.session_state.clear_trigger = False

if "results_df" not in st.session_state:
    st.session_state.results_df = None

if "resume_map" not in st.session_state:
    st.session_state.resume_map = {}

if "waiting_login" not in st.session_state:
    st.session_state.waiting_login = False

if "timer_start" not in st.session_state:
    st.session_state.timer_start = None

if "selected_candidates" not in st.session_state:
    st.session_state.selected_candidates = set()

if "checkbox_reset_counter" not in st.session_state:
    st.session_state.checkbox_reset_counter = 0

if "shortlist_checkbox_reset_counter" not in st.session_state:
    st.session_state.shortlist_checkbox_reset_counter = 0

# if "name_sort_top" not in st.session_state:
#     st.session_state.name_sort_top = "default"

# if "name_sort_filtered" not in st.session_state:
#     st.session_state.name_sort_filtered = "default"

# if "name_sort_short" not in st.session_state:
#     st.session_state.name_sort_short = "default"

# if "name_sort_rej" not in st.session_state:
#     st.session_state.name_sort_rej = "default"

# Resume
def get_resume_map_resumes_only(df):
    resumes = {}

    for _, row in df.iterrows():
        name = row.get("Name", "")
        resume_file = None

        if name:
            clean_name = name.replace(" ", "").replace(".", "").lower()
            filename_prefix = "naukri_" + clean_name

            pdf_file = None
            docx_file = None

            for file in os.listdir(RESUME_DIR):
                file_lower = file.lower()

                if file_lower.startswith(filename_prefix):
                    full_path = os.path.join(RESUME_DIR, file)

                    if file_lower.endswith(".pdf"):
                        pdf_file = full_path
                    elif file_lower.endswith((".docx", ".doc")):
                        docx_file = full_path

            resume_file = pdf_file if pdf_file else docx_file

        resumes[name] = resume_file

    return resumes

def get_resume_map_shortlisted(df):
    resumes = {}

    for _, row in df.iterrows():
        name = row.get("Name", "")
        resume_file = None

        if name:
            clean_name = name.replace(" ", "").replace(".", "").lower()
            filename_prefix = "naukri_" + clean_name

            pdf_file = None
            docx_file = None

            for file in os.listdir(SHORTLISTED_DIR):
                file_lower = file.lower()

                if file_lower.startswith(filename_prefix):
                    full_path = os.path.join(SHORTLISTED_DIR, file)

                    if file_lower.endswith(".pdf"):
                        pdf_file = full_path
                    elif file_lower.endswith((".docx", ".doc")):
                        docx_file = full_path

            resume_file = pdf_file if pdf_file else docx_file

        resumes[name] = resume_file

    return resumes

def move_resume_to_shortlisted(name):
    if not name:
        return

    clean_name = name.replace(" ", "").replace(".", "").lower()
    prefix = "naukri_" + clean_name

    for file in os.listdir(RESUME_DIR):
        file_lower = file.lower()

        if file_lower.startswith(prefix):
            src = os.path.join(RESUME_DIR, file)
            dst = os.path.join(SHORTLISTED_DIR, file)

            try:
                if os.path.exists(dst):
                    os.remove(dst)

                shutil.move(src, dst)

                print(f"[MOVE] {file}")

            except Exception as e:
                print("Move failed:", e)

def clear_resume_folder():
    for file in os.listdir(RESUME_DIR):
        file_path = os.path.join(RESUME_DIR, file)

        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print("[ERROR] Delete failed:", e)

def format_ist_date(date_val):
    if not date_val:
        return ""

    try:
        dt = pd.to_datetime(date_val, errors="coerce")

        if pd.isna(dt):
            return ""

        # Convert to IST
        dt = dt.tz_localize("UTC", ambiguous="NaT", nonexistent="NaT") if dt.tzinfo is None else dt
        dt = dt.tz_convert("Asia/Kolkata")

        return dt.strftime("%d/%m/%Y")
    except:
        return str(date_val)

# =========================
# UI
# =========================
st.set_page_config(page_title="HR APP", layout="wide")

st.title("Candidate Data Extraction and Evaluation System")
tab1, tab2, tab3, tab4 = st.tabs(["Search", "Shortlisted", "Rejected", "Settings"])

st.markdown("""
<style>
.stApp {
        background-image: url("https://wallpapers.com/images/hd/cute-light-blue-u229ckyqp6rhjqyr.jpg");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
/* Remove top padding completely */
.block-container {
    padding-top: 9rem !important;
}

/* Remove extra spacing above title */
h1 {
    margin-top: 0 !important;
}

/* Hide top right toolbar (Deploy, menu, etc.) */
[data-testid="stToolbar"] {
    display: none !important;
}

/* Target the default Streamlit header to match your cream theme */
[data-testid="stHeader"] {
    background-color: #fffae6 !important;
}

/* ── 1. The Header Shield (Fixed Title & Tabs) ── */

/* Pin Title (h1) */
[data-testid="stElementContainer"]:has(h1) {
    position: fixed !important;
    top: 0;
    left: 0;
    right: 0;
    height: 5.5rem;
    background-color: #fffae6;
    z-index: 9999;
    padding: 2rem 5rem 0rem 5rem;
    margin: 0 !important;
}

/* Pin Tab Buttons right below the title */
[data-testid="stTabs"] [role="tablist"] {
    position: fixed !important;
    top: 5.5rem;
    left: 0;
    right: 0;
    z-index: 9998;
    background-color: #fffae6;
    padding: 0.5rem 5rem !important;
    border-bottom: 1px solid #eee;
}

/* Force all vertical blocks back to zero gap to fix the table rows */
[data-testid="stVerticalBlock"] {
    gap: 0rem !important;
}

/* Restore minimal spacing ONLY for elements that are NOT table rows (like the prompt box) */
[data-testid="stElementContainer"]:not(:has([data-testid="stHorizontalBlock"])) {
    margin-bottom: 0.8rem !important;
}

/* ── Checkbox Padding ── */
[data-testid="stCheckbox"] {
    padding-left: 14px !important;
}

/* ── All rows get full border box ── */
[data-testid="stHorizontalBlock"] {
    gap: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    border: 1.5px solid #cccccc;
    border-bottom: none;
}

[data-testid="stHorizontalBlock"]:last-of-type {
    border-bottom: 1.5px solid #cccccc;
}

[data-testid="stColumn"] {
    border-right: 1.5px solid #cccccc !important;
    padding: 6px 12px !important;
}

[data-testid="stColumn"]:last-child {
    border-right: none !important;
}

/* ── Header ── */
[data-testid="stHorizontalBlock"]:first-of-type {
    background-color: #f0f2f6;
    border-bottom: 2px solid #999999 !important;
}

/* ── Remove gap globally to connect rows ── */
[data-testid="stVerticalBlock"] {
    gap: 0 !important;
}

/* ── Restore spacing for non-table elements ── */
[data-testid="stElementContainer"]:not(:has([data-testid="stHorizontalBlock"])) {
    margin-bottom: 0.75rem !important;
}

/* ── Zero out spacing for table row containers ── */
[data-testid="stElementContainer"]:has([data-testid="stHorizontalBlock"]) {
    margin: 0 !important;
    padding: 0 !important;
}

/* ── Remove borders from button/filter rows BUT NOT download buttons ── */
[data-testid="stHorizontalBlock"]:has([data-testid="stBaseButton-secondary"]):not(:has([data-testid="stDownloadButton"])),
[data-testid="stHorizontalBlock"]:has([data-testid="stSelectbox"]),
[data-testid="stHorizontalBlock"]:has([data-testid="stMultiSelect"]),
[data-testid="stHorizontalBlock"]:has([data-testid="stNumberInput"]) {
    border: none !important;
    background: none !important;
}

[data-testid="stHorizontalBlock"]:has([data-testid="stBaseButton-secondary"]):not(:has([data-testid="stDownloadButton"])) [data-testid="stColumn"],
[data-testid="stHorizontalBlock"]:has([data-testid="stSelectbox"]) [data-testid="stColumn"],
[data-testid="stHorizontalBlock"]:has([data-testid="stMultiSelect"]) [data-testid="stColumn"],
[data-testid="stHorizontalBlock"]:has([data-testid="stNumberInput"]) [data-testid="stColumn"] {
    border: none !important;
}

/* Remove table styling ONLY for ZIP download row */
[data-testid="stHorizontalBlock"]:has([data-testid="stDownloadButton"]):has([data-testid="stColumn"]:nth-child(3)):not(:has([data-testid="stColumn"]:nth-child(4))) {
    border: none !important;
    background: none !important;
}

[data-testid="stHorizontalBlock"]:has([data-testid="stDownloadButton"]):has([data-testid="stColumn"]:nth-child(3)):not(:has([data-testid="stColumn"]:nth-child(4))) [data-testid="stColumn"] {
    border: none !important;
}

/* ── Hover ── */
[data-testid="stHorizontalBlock"]:hover {
    background-color: #f7f7f7;
}

[data-testid="stHorizontalBlock"]:first-of-type:hover {
    background-color: #f0f2f6;
}

/* Fix tab button alignment */
[data-testid="stTabs"] [role="tab"] {
    display: flex !important;
    align-items: center !important;   /* vertical centering */
    justify-content: center;
    height: 2.5rem !important;        /* consistent hitbox */
    padding: 0.4rem 1rem !important;
    margin: 0 !important;
}

/* Fix tab text positioning */
[data-testid="stTabs"] [role="tab"] p {
    margin: 0 !important;
    line-height: 1 !important;
}

/* Move tab TEXT slightly down */
[data-testid="stTabs"] [role="tab"] p {
    transform: translateY(10px);   /* try 2px–5px if needed */
}

</style>
""", unsafe_allow_html=True)

def clean_rejected_candidates():
    df_rej = get_sheet4_data()
    headers = df_rej.columns.tolist() if not df_rej.empty else sheet4.row_values(1)

    if not df_rej.empty and "RejectedOn" in df_rej.columns:

        df_rej["RejectedOn"] = pd.to_datetime(
            df_rej["RejectedOn"], errors="coerce"
        )

        settings = load_settings()

        months = settings.get("rej_months", 6)
        days = settings.get("rej_days", 0)

        if months == 0 and days == 0:
            sheet4.clear()
            sheet4.append_row(headers)
            return
            
        cutoff = pd.Timestamp.now(tz="UTC") - pd.DateOffset(
            months=months,
            days=days
        )

        # FILTER
        df_rej = df_rej[df_rej["RejectedOn"] > cutoff]

        # REWRITE SHEET
        sheet4.clear()
        sheet4.append_row(headers)

        if not df_rej.empty:

            for _, row in df_rej.iterrows():
                cleaned_row = [
                    val.isoformat() if isinstance(val, pd.Timestamp) else val
                    for val in row
                ]
                sheet4.append_row(cleaned_row)

with tab1:

    col1, col2 = st.columns([4, 1.5])

    with col1:
        if "prompt_text" not in st.session_state:
            st.session_state.prompt_text = ""

        if st.session_state.clear_trigger:
            st.session_state.prompt_text = ""
            st.session_state.clear_trigger = False

        prompt = st.text_area("Enter Prompt", height=120, key="prompt_text")
    with col2:
        cand_num = st.number_input(
            "No. of Candidates",
            min_value=1,
            max_value=100,
            step=1,
            value=10
        )

        active_in_options = [
            "All resumes",
            "1 day", "3 days", "7 days", "15 days", "30 days",
            "2 months", "3 months", "6 months", "1 year",
            "8 to 15 days", "16 to 30 days",
            "1 to 2 months", "2 to 3 months",
            "3 to 6 months", "6 to 12 months",
            "1 year+"
        ]

        active_in = st.selectbox(
            "Active In",
            options=active_in_options,
            index=active_in_options.index("6 months")  # default
        )

    # =========================
    # VALIDATE PROMPT
    # =========================
    def valid_prompt(text):
        pattern = r'^[a-zA-Z0-9\s,./\\"-]*$'
        return re.match(pattern, text) is not None


    # =========================
    # GET TOP CANDIDATES
    # =========================
    @st.cache_data(ttl=60)
    def get_top_candidates():

        data = sheet1.get_all_records()
        df = pd.DataFrame(data)

        if df.empty:
            return pd.DataFrame(), {}

        df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
        df = df.dropna(subset=["rank"])
        df = df.sort_values("rank")
        df = df[df["rank"] <= 10]

        resumes = get_resume_map_resumes_only(df)

        return df, resumes


    # =========================
    # EXPORT ZIP
    # =========================
    def create_export_zip(df, resumes):

        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w") as zip_file:

            export_rows = []

            for _, row in df.iterrows():

                name = row["Name"]
                resume = resumes.get(name)

                resume_name = ""

                if resume and os.path.exists(resume):
                    zip_file.write(resume)
                    resume_name = resume

                export_rows.append({
                    "Rank": row["rank"],
                    "Name": name,
                    "ProfileURL": row["ProfileURL"],
                    "ReceivedAt": row["ReceivedAt"],
                    "ResumeFile": resume_name
                })

            export_df = pd.DataFrame(export_rows)

            excel_buffer = io.BytesIO()
            export_df.to_excel(excel_buffer, index=False)

            zip_file.writestr("candidate_results.xlsx", excel_buffer.getvalue())

        zip_buffer.seek(0)
        return zip_buffer


    # =========================
    # CLEAR SHEET1
    # =========================
    def clear_candidates():

        rows = sheet1.get_all_values()

        if len(rows) > 1:
            sheet1.batch_clear([f"A2:Z{len(rows)}"])


    # =========================
    # START BUTTON
    # =========================
    col_btn1, col_btn2 = st.columns([1,8])

    with col_btn1:
        next_clicked = st.button("Next")

    with col_btn2:
        if st.button("Clear"):
            st.session_state.clear_trigger = True
            st.session_state.results_df = None
            st.session_state.resume_map = {}
            st.session_state.filtered_df = None
            st.session_state.selected_candidates = set()
            st.session_state.selected_locations = []
            st.session_state.checkbox_reset_counter += 1
            st.rerun()
    
    if next_clicked:

        st.session_state.active_in = active_in

        if not prompt.strip():
            st.warning("Please enter a prompt.")

        elif not valid_prompt(prompt):
            st.error("Invalid input.")

        elif cand_num <= 0:
            st.warning("Please enter valid number of candidates.")

        else:              
            # ---- LENGTH CHECK ----
            cleaned = prompt.replace('"', '').replace(',', '')
            cleaned = ''.join(cleaned.split())  # remove spaces
            length = len(cleaned)

            if length > 200:
                st.error(f"Prompt too long.. ({length} chars). Reduce it to less than 200.")
                st.stop()

            # CONTINUE FLOW
            st.session_state.waiting_login = True
            st.session_state.cand_num = cand_num


    # =========================
    # LOGIN FORM
    # =========================
    if st.session_state.waiting_login:

        st.subheader("Enter Credentials")

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        # INIT MESSAGE STATE
        if "status_message" not in st.session_state:
            st.session_state.status_message = ("", "#000000")

        def update_status(msg, color, box):
            st.session_state.status_message = (msg, color)
            html = f"""
            <div style="
                background-color:#e8f4fd;
                padding:10px;
                border-radius:6px;
                border-left:5px solid #3498db;
                font-weight:500;
                color:{color};
            ">
                {msg}
            </div>
            """
            box.markdown(html, unsafe_allow_html=True)

        if st.button("Start Execution"):
            
            clear_candidates()
            clear_resume_folder()

            if not username or not password:
                st.warning("Please enter username and password.")

            else:
                clean_rejected_candidates()

                requests.post(
                    "http://localhost:5000/set_credentials",
                    json={
                        "email": username,
                        "password": password
                    }
                )

                try:
                    sheet2.update_cell(2, 10, cand_num)
                    sheet2.update_cell(2, 3, st.session_state.active_in)
                except Exception as e:  # this exception wont work
                    st.error("⚠️ Google Sheets API issue. Please reauthorize in n8n.")
                    st.warning("Please restart the app after fixing the issue.")
                    st.stop()

                payload = {"prompt": prompt}

                response = requests.post(WEBHOOK_URL, json=payload)

                if response.status_code == 200:

                    st.session_state.timer_start = time.time()

                    # SINGLE BOX
                    status_placeholder = st.empty()

                    # RESET + FIRST MESSAGE
                    update_status("Execution started...", "#2ecc71", status_placeholder)

                    while True:

                        if st.session_state.google_sheet_error:
                            update_status("⚠️ Google Sheets Error (Reauthorization Required in n8n)","#e74c3c",status_placeholder)
                            st.session_state.google_sheet_error = False
                            break

                        state2 = sheet2.cell(2, 4).value

                        if state2 == "Launching":
                            update_status("🚀 Session Started...", "#3498db", status_placeholder)

                        elif state2 == "Searching":
                            update_status("🔍 Searching and Filtering Out Candidates...", "#9b59b6", status_placeholder)

                        elif state2 == "Processing":
                            update_status("📄 Extracting Profile Details from Candidates...", "#f39c12", status_placeholder)

                        elif state2 == "Ranking":
                            update_status("📊 Processing and Ranking Candidates...", "#e74c3c", status_placeholder)

                        elif state2 == "Gemini API Quota Exceeded":
                            update_status("⚠️ Gemini API Quota Exceeded", "#e74c3c", status_placeholder)
                            sheet2.update_cell(2, 4, "ended") # if it doesn't change to ended, add delay before updating
                            break

                        elif state2 == "Error: n8n":
                            update_status("⚠️ Error: n8n", "#e74c3c", status_placeholder)
                            sheet2.update_cell(2, 4, "ended") # if it doesn't change to ended, add delay before updating
                            break

                        elif state2 == "Incorrect":
                            update_status("⚠️ Incorrect Username or Password", "#e74c3c", status_placeholder)
                            sheet2.update_cell(2, 4, "ended") # if it doesn't change to ended, add delay before updating
                            break

                        # =========================
                        # OTP INPUT UI
                        # =========================
                        if state2 == "otp_req":

                            update_status("OTP required. Please enter OTP (valid for 10 minutes)", "#e67e22", status_placeholder)

                            if "otp_start_time" not in st.session_state:
                                st.session_state.otp_start_time = time.time()
                                st.session_state.otp_sent = False
                                st.session_state.otp_expired = False

                            remaining = 600 - (time.time() - st.session_state.otp_start_time)

                            if remaining <= 0:
                                st.session_state.otp_expired = True

                            if st.session_state.otp_expired:
                                update_status("OTP expired. Please restart process.", "#c0392b", status_placeholder)

                            else:
                                update_status(f"Time left: {int(remaining)} seconds", "#16a085", status_placeholder)

                                otp_input = st.text_input("Enter OTP", key="otp_input")

                                if (
                                    otp_input
                                    and len(otp_input) == 6
                                    and not st.session_state.otp_sent
                                ):
                                    try:
                                        response = requests.post(
                                            "http://localhost:5000/set_otp",
                                            json={"otp": otp_input}
                                        )

                                        if response.status_code == 200:
                                            st.session_state.otp_sent = True
                                            update_status("OTP sent to automation", "#27ae60", status_placeholder)
                                            st.session_state.otp_input = ""
                                        else:
                                            update_status("Failed to send OTP", "#e74c3c", status_placeholder)

                                    except:
                                        update_status("Error sending OTP", "#e74c3c", status_placeholder)

                        if state2 == "posting":

                            try:
                                for win in gw.getAllWindows():
                                    if "Firefox" in win.title:
                                        win.minimize()
                            except:
                                pass

                            df, resumes = get_top_candidates()

                            sheet2.update_cell(2, 4, "ended")
                            os.system('taskkill /f /im firefox.exe /t')
                            st.session_state.results_df = df
                            st.session_state.resume_map = resumes

                            if "otp_start_time" in st.session_state:
                                del st.session_state.otp_start_time

                            st.session_state.otp_sent = False
                            st.session_state.otp_expired = False

                            elapsed = int(time.time() - st.session_state.timer_start)

                            minutes = elapsed // 60
                            seconds = elapsed % 60

                            update_status(
                                f"Execution completed in {minutes} min {seconds} sec",
                                "#2ecc71",
                                status_placeholder
                            )

                            break

                        time.sleep(5)

                else:
                    st.error("Failed to start ranking.")


    # =========================
    # DISPLAY ORIGINAL RESULTS
    # =========================
    df = st.session_state.results_df
    resumes = st.session_state.resume_map

    if df is not None and not df.empty:

        st.subheader("Top Candidates")
        st.markdown("---")
        st.subheader("Apply Additional Filters")

        col1, col2, col3, col4a, col4b = st.columns([4, 4, 4, 2, 2])

        # Gender
        gender_filter = col1.selectbox("Gender", ["All", "Male", "Female"])


        # =========================
        # LOCATION FILTER
        # =========================

        if "selected_locations" not in st.session_state:
            st.session_state.selected_locations = []

        selected_locations = st.session_state.selected_locations

        if "Location" in df.columns:

            # Extract unique locations
            all_locations = sorted({
                x.strip()
                for loc in df["Location"].dropna()
                for x in loc.split(",")
                if x.strip()
            })

            # SEARCHABLE MULTISELECT
            selected_locations = [loc for loc in selected_locations if loc in all_locations]

            selected_locations = col2.multiselect(
                "Select Prefered Location",
                options=all_locations,
                default=selected_locations,
                key="location_multiselect"
            )

            # Save selection
            st.session_state.selected_locations = selected_locations


        # =========================
        # EXPERIENCE
        # =========================

        exp_type = col3.selectbox("Experience Type", ["None", "Minimum", "Maximum"])

        exp_years = col4a.number_input("Years", min_value=0, max_value=50, value=0)
        exp_months = col4b.number_input("Months", min_value=0, max_value=11, value=0)

        input_exp_months = exp_years * 12 + exp_months


        # =========================
        # APPLY FILTER BUTTON
        # =========================

        # Initialize session state
        if "filtered_df" not in st.session_state:
            st.session_state.filtered_df = None

        # BUTTON → ONLY FILTER + SAVE
        col_left, col_center, col_right = st.columns([3.7, 2, 3])
        with col_center:
            if st.button("Apply Filters"):

                filtered_df = df.copy()

                # Gender filter
                if gender_filter != "All" and "Gender" in filtered_df.columns:
                    filtered_df = filtered_df[
                        filtered_df["Gender"].str.lower() == gender_filter.lower()
                    ]

                # LOCATION FILTER
                if selected_locations and "Location" in filtered_df.columns:

                    def location_match(row_loc):
                        if pd.isna(row_loc):
                            return False
                        row_locs = [x.strip().lower() for x in row_loc.split(",")]
                        return any(loc.lower() in row_locs for loc in selected_locations)

                    filtered_df = filtered_df[
                        filtered_df["Location"].apply(location_match)
                    ]

                # EXPERIENCE FILTER
                if exp_type != "None" and "Experience(months)" in filtered_df.columns:

                    filtered_df["Experience(months)"] = pd.to_numeric(
                        filtered_df["Experience(months)"], errors="coerce"
                    )

                    if exp_type == "Minimum" and input_exp_months > 0:
                        filtered_df = filtered_df[
                            filtered_df["Experience(months)"] >= input_exp_months
                        ]

                    elif exp_type == "Maximum" and input_exp_months > 0:
                        filtered_df = filtered_df[
                            filtered_df["Experience(months)"] <= input_exp_months
                        ]

                #  SAVE RESULT
                st.session_state.filtered_df = filtered_df

        st.markdown('<div class="header-border">', unsafe_allow_html=True)
        header = st.columns([1,1,3,3,3,3,3])
        header[0].markdown("**Select**")
        header[1].markdown("**Rank**")
        header[2].markdown("**Name**")
        header[3].markdown("**Email**")
        header[4].markdown("**Phno**")
        header[5].markdown("**ReceivedAt**")
        header[6].markdown(
            "<div style='padding-left:16px; font-weight:bold;'>Resume</div>",
            unsafe_allow_html=True
        )

        display_df = st.session_state.filtered_df if st.session_state.filtered_df is not None else df
        display_df = display_df.sort_values("rank")
        display_df["UID"] = display_df["ProfileURL"].apply(get_uid)

        for i, row in display_df.iterrows():

            cols = st.columns([1,1,3,3,3,3,3])

            name = row["Name"]
            email = row.get("Email", "")
            phone = row.get("Phno", "")
            profile_url = row["ProfileURL"]
            resume = resumes.get(name)
            uid = row["UID"]
            
            checked = cols[0].checkbox("", key=f"select_{uid}_{st.session_state.checkbox_reset_counter}", value=(uid in st.session_state.selected_candidates))

            if checked:
                st.session_state.selected_candidates.add(uid)
            else:
                st.session_state.selected_candidates.discard(uid)

            cols[1].write(int(row["rank"]))
            cols[2].write(name)
            cols[3].write(email)
            cols[4].write(phone)
            cols[5].write(format_ist_date(row["ReceivedAt"]))

            if resume and os.path.exists(resume):
                with open(resume, "rb") as f:
                    cols[6].download_button("Download", f, file_name=resume, mime = "application/pdf" if resume.lower().endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document", key=f"{resume}_{i}")
            else:
                cols[6].markdown(
                "<div style='padding-left:14px;'>Not Found</div>",
                unsafe_allow_html=True
            )

        col_left, col_center, col_right = st.columns([3, 3.42, 1.78])
        with col_left:
            
            if st.button("Shortlist Selected Candidates", key="shortlist_btn"):

                if not st.session_state.selected_candidates:
                    st.warning("No candidates selected.")
                else:
                    selected_rows = display_df[display_df["UID"].isin(st.session_state.selected_candidates)]

                    headers = sheet3.row_values(1)
                    existing = get_sheet3_data()
                    existing_uids = set(
                        existing["ProfileURL"].apply(get_uid)
                    ) if not existing.empty else set()

                    for _, row in selected_rows.iterrows():
                        row_data = row.to_dict()
                        move_resume_to_shortlisted(row["Name"])
                        row_data["Status"] = "Shortlisted"

                        if get_uid(row["ProfileURL"]) not in existing_uids:
                            ordered_row = [row_data.get(col, "") for col in headers]
                            sheet3.append_row(ordered_row)

                    remove_shortlisted(selected_rows)
                    st.cache_data.clear()
                    fresh_df, fresh_resumes = get_top_candidates()
                    st.session_state.results_df = fresh_df
                    st.session_state.resume_map = fresh_resumes
                    st.session_state.filtered_df = None
                    st.success("Moved to Shortlisted")                    
                    st.session_state.selected_candidates = set()
                    st.session_state.checkbox_reset_counter += 1
                    st.rerun()
                    

        with col_center:
            if st.button("Send Email to Selected Candidates", key="email_btn_top"):
                if not st.session_state.selected_candidates:
                    st.warning("No candidates selected.")
                else:
                    selected_rows = display_df[display_df["UID"].isin(st.session_state.selected_candidates)]
                    sheet3_df = get_sheet3_data()
                    existing_uids = set(
                        sheet3_df["ProfileURL"].apply(get_uid)
                    ) if not sheet3_df.empty else set()

                    headers = sheet3.row_values(1)

                    for _, row in selected_rows.iterrows():
                        send_email(time.strftime("%Y-%m-%d"), row["Name"])
                        row_data = row.to_dict()
                        move_resume_to_shortlisted(row["Name"])
                        row_data["Status"] = "Shortlisted"
                        if get_uid(row["ProfileURL"]) not in existing_uids:
                            ordered_row = [row_data.get(col, "") for col in headers]
                            sheet3.append_row(ordered_row)

                    remove_shortlisted(selected_rows)
                    st.cache_data.clear()
                    fresh_df, fresh_resumes = get_top_candidates()
                    st.session_state.results_df = fresh_df
                    st.session_state.resume_map = fresh_resumes
                    st.session_state.filtered_df = None
                    st.success("Email sent!")                    
                    st.session_state.selected_candidates = set()
                    st.session_state.checkbox_reset_counter += 1
                    st.rerun()

        with col_right:
            if st.button("Reset Filters"):
                st.session_state.filtered_df = None
                st.session_state.selected_locations = []
                st.session_state.selected_candidates = set()
                st.session_state.checkbox_reset_counter += 1
                st.rerun()

        zip_col_left, zip_col_center, zip_col_right = st.columns([3.1, 2, 3.26])

        with zip_col_center:

            zip_data = create_export_zip(display_df, resumes)

            st.download_button(
                label="Download ZIP (Resumes + Excel)",
                data=zip_data,
                file_name="candidates_export.zip",
                mime="application/zip"
            )           

    # =========================
    # CLEAR BUTTON
    # =========================
    # if st.button("Clear Candidates & Stop"):

    #     clear_candidates()

    #     st.session_state.results_df = None
    #     st.session_state.resume_map = {}
    #     st.session_state.waiting_login = False
    #     st.session_state.timer_start = None
    #     st.session_state.selected_candidates = set()

    #     st.success("Candidates cleared from Sheet1.")
    #     st.rerun()


with tab2:

    st.subheader("Shortlisted Candidates")

    df_short = get_sheet3_data()
    resumes_short = get_resume_map_shortlisted(df_short)
    
    if not df_short.empty and "ProfileURL" in df_short.columns:

        df_short["UID"] = df_short["ProfileURL"].apply(get_uid)

    if st.button("🔄", key="refresh_short"):
        st.cache_data.clear()
        st.rerun()

    if not df_short.empty:

        selected_shortlisted = set()

        st.markdown('<div class="header-border">', unsafe_allow_html=True)
        header = st.columns([1,3,3,3,3,3])
        header[0].markdown("**Select**")
        header[1].markdown("**Name**")
        header[2].markdown("**Email**")
        header[3].markdown("**Phone**")
        header[4].markdown("**ReceivedAt**")
        header[5].markdown(
            "<div style='padding-left:16px; font-weight:bold;'>Resume</div>",
            unsafe_allow_html=True
        )

        for idx, row in df_short.iterrows():

            cols = st.columns([1,3,3,3,3,3])

            profile_url = row["ProfileURL"]
            uid = get_uid(profile_url)

            checked = cols[0].checkbox(
                "",
                key=f"short_{uid}_{idx}_{st.session_state.shortlist_checkbox_reset_counter}"
            )

            if checked:
                selected_shortlisted.add(uid)

            name = row["Name"]
            email = row.get("Email", "")
            phone = row.get("Phno", "")

            cols[1].write(name)
            cols[2].write(email)
            cols[3].write(phone)
            cols[4].write(format_ist_date(row.get("ReceivedAt", "")))

            resume = resumes_short.get(name)

            if resume and os.path.exists(resume):
                with open(resume, "rb") as f:
                    cols[5].download_button(
                        "Download",
                        f,
                        file_name=resume,
                        mime = "application/pdf" if resume.lower().endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"short_{resume}_{idx}"
                    )
            else:
                cols[5].markdown(
                    "<div style='padding-left:14px;'>Not Found</div>",
                    unsafe_allow_html=True
                )

        col_left, col_center, col_right, col_reset = st.columns([2.6, 2, 2, 2.02])

        with col_left:
            if st.button("Send Email to Selected Candidates", key="email_shortlisted"):

                if not selected_shortlisted:
                    st.warning("No candidates selected.")
                else:
                    for uid in selected_shortlisted:

                        filtered = df_short[df_short["UID"] == uid]

                        if not filtered.empty:
                            row = filtered.iloc[0]
                        else:
                            continue

                        send_email(time.strftime("%Y-%m-%d"), row["Name"])

                    st.success("Emails sent!")

        with col_center:
            if st.button("Reject Selected Candidates"):

                rej_df = get_sheet4_data()
                headers = rej_df.columns.tolist() if not rej_df.empty else sheet4.row_values(1)
                existing_uids = set(
                    rej_df["ProfileURL"].apply(get_uid)
                ) if not rej_df.empty else set()
                all_data = df_short.to_dict(orient="records")
                
                for uid in selected_shortlisted:

                    row = df_short[
                        df_short["UID"] == uid
                    ].iloc[0]
                    row_data = row.to_dict()
                    row_data["Status"] = "Rejected"
                    row_data["RejectedOn"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")

                    if get_uid(row["ProfileURL"]) not in existing_uids:
                        ordered_row = [row_data.get(col, "") for col in headers]
                        sheet4.append_row(ordered_row)


                updated_data = [
                    r for r in all_data
                    if get_uid(r["ProfileURL"]) not in selected_shortlisted
                ]

                sheet3.clear()

                if all_data:
                    sheet3.append_row(list(all_data[0].keys()))

                rows = [list(r.values()) for r in updated_data]
                if rows:
                    sheet3.append_rows(rows)

                st.success("Moved to Rejected")
                st.cache_data.clear()
                st.rerun()

        with col_right:
            if st.button("Remove Selected Candidates"):

                all_data = df_short.to_dict(orient="records")

                updated_data = [
                    r for r in all_data
                    if get_uid(r["ProfileURL"]) not in selected_shortlisted
                ]

                sheet3.clear()

                if all_data:
                    sheet3.append_row(list(all_data[0].keys()))

                rows = [list(r.values()) for r in updated_data]
                if rows:
                    sheet3.append_rows(rows)

                st.success("Removed")
                st.cache_data.clear()
                st.rerun()    

        with col_reset:
            if st.button("Reset Selection", key="reset_shortlisted"):
                st.session_state.shortlist_checkbox_reset_counter += 1
                st.rerun()
        
        # =========================
        # ADD CANDIDATE (MANUAL)
        # =========================

        if "show_add_candidate" not in st.session_state:
            st.session_state.show_add_candidate = False

        if st.button("➕ Add Candidate"):
            st.session_state.show_add_candidate = not st.session_state.show_add_candidate

        if st.session_state.show_add_candidate:

            st.markdown("### Add New Candidate")

            col1, col2 = st.columns(2)

            with col1:
                new_name = st.text_input("Name")
                new_email = st.text_input("Email")

            with col2:
                new_phone = st.text_input("Phone")
                new_resume = st.file_uploader("Upload Resume", type=["pdf", "docx"])

            if st.button("Add Candidate to Shortlisted"):

                if not new_name.strip():
                    st.warning("Name is required.")
                else:
                    headers = sheet3.row_values(1)

                    # Save resume
                    resume_filename = ""
                    if new_resume is not None:
                        resume_filename = f"Naukri_{new_name.replace(' ', '')}.{new_resume.name.split('.')[-1]}"
                        files = {"file": (new_resume.name, new_resume.getvalue())}
                        data = {"name": new_name}

                        response = requests.post(
                            "http://192.168.127.180:5001/upload_resume",
                            files=files,
                            data=data
                        )

                        if response.status_code == 200:
                            st.success("Resume uploaded to server!")
                        else:
                            st.error("Failed to upload resume.")

                    # Create row
                    row_data = {col: "" for col in headers}

                    row_data["Name"] = new_name
                    row_data["Email"] = new_email
                    row_data["Phno"] = new_phone
                    row_data["Status"] = "Shortlisted"
                    row_data["ReceivedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")

                    # ProfileURL fallback (needed for UID logic)
                    row_data["ProfileURL"] = f"manual_{new_name}_{int(time.time())}"

                    ordered_row = [row_data.get(col, "") for col in headers]
                    sheet3.append_row(ordered_row)

                    st.success("Candidate added successfully!")

                    # refresh UI
                    st.session_state.show_add_candidate = False
                    st.cache_data.clear()
                    st.rerun()

with tab3:

    st.subheader("Rejected Candidates")

    df_rej = get_sheet4_data()
    resumes_rej = get_resume_map_shortlisted(df_rej)

    if st.button("🔄", key="refresh_rej"):
        st.cache_data.clear()
        st.rerun()

    if not df_rej.empty:

        st.markdown('<div class="header-border">', unsafe_allow_html=True)
        header = st.columns([3,3,3,3,3,3])
        header[0].markdown("**Name**")
        header[1].markdown("**Email**")
        header[2].markdown("**Phone**")
        header[3].markdown("**ReceivedAt**")
        header[4].markdown("**RejectedOn**")
        header[5].markdown(
            "<div style='padding-left:16px; font-weight:bold;'>Resume</div>",
            unsafe_allow_html=True
        )

        for _, row in df_rej.iterrows():

            cols = st.columns([3,3,3,3,3,3])

            cols[0].write(row["Name"])
            cols[1].write(row.get("Email", ""))
            cols[2].write(row.get("Phno", ""))
            cols[3].write(format_ist_date(row.get("ReceivedAt", "")))
            cols[4].write(format_ist_date(row.get("RejectedOn", "")))
            name = row["Name"]
            resume = resumes_rej.get(name)

            if resume and os.path.exists(resume):
                with open(resume, "rb") as f:
                    cols[5].download_button(
                        "Download",
                        f,
                        file_name=resume,
                        mime = "application/pdf" if resume.lower().endswith(".pdf") else "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"rej_{resume}_{name}"
                    )
            else:
                cols[5].markdown(
                    "<div style='padding-left:14px;'>Not Found</div>",
                    unsafe_allow_html=True
                )

with tab4:

    st.subheader("Settings")

    settings = load_settings()

    st.info(f"Current expiry: {settings['rej_months']} months, {settings['rej_days']} days")

    col1, col2 = st.columns(2)

    with col1:
        rej_months = st.number_input(
            "Expiry - Months",
            min_value=0,
            max_value=24,
            value=settings.get("rej_months", 6)
        )

    with col2:
        rej_days = st.number_input(
            "Expiry - Days",
            min_value=0,
            max_value=31,
            value=settings.get("rej_days", 0)
        )

    if st.button("Save Settings"):
        save_settings({
            "rej_months": rej_months,
            "rej_days": rej_days
        })
        clean_rejected_candidates()
        st.cache_data.clear()
        st.success("Settings saved successfully!")
        st.rerun()
        
