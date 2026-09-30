import pygetwindow as gw
import subprocess
import time
import os
import pyautogui
import gspread
from google.oauth2.service_account import Credentials
import ctypes
import sys
from flask import Flask, request, jsonify

otp_value = None
email_value = None
password_value = None

# =========================
# ADMIN CHECK
# =========================

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

pyautogui.FAILSAFE = True


# =========================
# CONFIG
# =========================

SERVICE_ACCOUNT_FILE = r"C:\Users\Admin\naukri_automation\soch-496111-1c5abfdf4dae.json"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

SPREADSHEET_NAME = "Naukri Candidates"
CONTROL_SHEET_NAME = "Sheet2"


# =========================
# GOOGLE SHEETS
# =========================

creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES
)

client = gspread.authorize(creds)
spreadsheet = client.open(SPREADSHEET_NAME)
control_sheet = spreadsheet.worksheet(CONTROL_SHEET_NAME)


# =========================
# SAFE LOCATE
# =========================

def safe_locate(image, confidence=0.8):
    try:
        return pyautogui.locateOnScreen(image, confidence=confidence)
    except Exception as e:
        print(f"[SAFE_LOCATE ERROR] {os.path.basename(image)} →", repr(e))
        return None


# =========================
# WAIT FOR IMAGE
# =========================

def wait_for_image(image_path, timeout=10, confidence=0.7):
    start = time.time()
    while time.time() - start < timeout:
        location = safe_locate(image_path, confidence)
        if location:
            return location
        time.sleep(0.5)
    return None


# =========================
# CLOSE LAUNCHER
# =========================

def close_naukri_launcher():
    try:
        print("Closing Naukri Launcher...")
        os.system('taskkill /f /im "Naukri Launcher.exe" /t')
    except Exception as e:
        print("Error:", e)


# =========================
# MAIN AUTOMATION
# =========================

def run_launcher_automation():

    print("Starting launcher automation...")

    vscode_windows = gw.getWindowsWithTitle("Visual Studio Code")
    if vscode_windows:
        vscode_windows[0].minimize()

    time.sleep(1)

    subprocess.run("schtasks /run /tn NaukriLauncherTask", shell=True)
    time.sleep(10)

    base_dir = os.path.dirname(os.path.abspath(__file__))

    email_empty_img = os.path.join(base_dir, "email_empty3.png")  # email_empty(1600x900)2.png
    password_empty_img = os.path.join(base_dir, "password_empty3.png")  # password_empty(1600x900)2.png
    login_button_img = os.path.join(base_dir, "login_button3.png")  # login_button(1600x900).png
    otp_boxes_img = os.path.join(base_dir, "otp.png")  # otp(1600x900).png
    logout_img = os.path.join(base_dir, "logout3.png")  # logout(1600x900).png
    incorrect_img = os.path.join(base_dir, "incorrect.png")

    pyautogui.moveTo(300, 300)

    print("Step: Logout check")

    logout_location = safe_locate(logout_img)

    if logout_location:
        print("logoutdetected")
        pyautogui.click(pyautogui.center(logout_location))
        time.sleep(3)

    print("Step: Email")

    email_empty = safe_locate(email_empty_img)
    if email_empty:
        print("emaildetected")
        pyautogui.click(pyautogui.center(email_empty))
        global email_value
        EMAIL = email_value
        if not EMAIL:
            return "Email not received"
        pyautogui.write(EMAIL, interval=0.05)

    print("Step: Password")

    password_empty = safe_locate(password_empty_img)
    if password_empty:
        print("pwdetected")
        pyautogui.click(pyautogui.center(password_empty))
        global password_value
        PASSWORD = password_value
        if not PASSWORD:
            return "Password not received"
        pyautogui.write(PASSWORD, interval=0.05)

    print("Step: Login")

    login_location = wait_for_image(login_button_img, timeout=5, confidence=0.8)
    if login_location:
        pyautogui.click(pyautogui.center(login_location))
    else:
        return "Login button not found"

    time.sleep(2)

    incorrect_location = wait_for_image(incorrect_img,timeout=2,confidence=0.8)

    if incorrect_location:
        print("Incorrect username or password detected")

        control_sheet.update_cell(2, 4, "Incorrect")

        close_naukri_launcher()

        return "Incorrect credentials"

    otp_location = wait_for_image(otp_boxes_img, timeout=3, confidence=0.6)

    if otp_location:
        print("OTP required")

        # notify Streamlit
        control_sheet.update_cell(2, 4, "otp_req")

        global otp_value

        start = time.time()
        otp = None

        while time.time() - start < 600:
            if otp_value is not None:
                otp = otp_value
                otp_value = None
                break
            time.sleep(1)

        if otp is not None:
            left_x = otp_location.left + 10
            center_y = otp_location.top + otp_location.height // 2
            pyautogui.click(left_x, center_y)
            pyautogui.write(str(otp), interval=0.1)
        else:
            return "OTP timeout"

    time.sleep(2)
    close_naukri_launcher()
    return "Automation completed"

def click_view_phone_button():

    print("Searching for view phone button")

    location = None

    for _ in range(5):
        location = pyautogui.locateOnScreen(
            VIEW_PHONE_IMG,
            confidence=0.8
        )
        if location:
            break
        time.sleep(1)

    if location:
        center = pyautogui.center(location)
        pyautogui.moveTo(center, duration=0.3)
        pyautogui.click()
        print("View phone button clicked")
        return "View phone button clicked"

    else:
        print("View phone button not found")
        return "View phone button not found"

def click_download_button():

    print("Searching for download button")

    location = None

    # try multiple times
    for _ in range(5):
        location = pyautogui.locateOnScreen(
            DOWNLOAD_IMG,
            confidence=0.8
        )
        if location:
            break
        time.sleep(1)

    if location:
        center = pyautogui.center(location)
        pyautogui.moveTo(center, duration=0.3)
        pyautogui.click()
        print("Download button clicked")
        return "Download button clicked"

    else:
        print("Download button not found")
        return "Download button not found"

# =========================
# FLASK API
# =========================

app = Flask(__name__)

@app.route("/run", methods=["POST"])
def run():
    try:
        # CHECK STATE2 (D2 column = col 4)
        state2 = control_sheet.cell(2, 4).value

        if state2 != "ended":
            return jsonify({
                "status": "skipped",
                "message": f"Automation not run. Current state: {state2}"
            })

        # RUN ONLY IF ENDED
        control_sheet.update_cell(2, 4, "Launching")
        result = run_launcher_automation()

        return jsonify({
            "status": "success",
            "message": result
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route("/set_credentials", methods=["POST"])
def set_credentials():
    global email_value, password_value
    data = request.json
    email_value = data.get("email")
    password_value = data.get("password")
    return jsonify({"status": "received"})

@app.route("/set_otp", methods=["POST"])
def set_otp():
    global otp_value
    data = request.json
    otp_value = data.get("otp")
    print("OTP received from Streamlit:", otp_value)
    return jsonify({"status": "received"})

if __name__ == "__main__":
    print("Python automation server running on http://localhost:5000")
    app.run(host="0.0.0.0", port=5000)
