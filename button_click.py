import os
import time
import pyautogui
from flask import request, Flask, jsonify

DOWNLOAD_IMG = r"C:\Users\Admin\naukri_automation\download_button.png"
VIEW_PHONE_IMG = r"C:\Users\Admin\naukri_automation\phone_button.png"
UPLOAD_FOLDER = "shortlisted&rejected"

pyautogui.FAILSAFE = True

# =========================
# MAIN FUNCTION
# =========================

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

@app.route("/view-phone", methods=["POST"])
def run_view_phone():
    try:
        result = click_view_phone_button()
        return jsonify({
            "status": "success",
            "message": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route("/download", methods=["POST"])
def run_download():
    try:
        result = click_download_button()
        return jsonify({
            "status": "success",
            "message": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route("/upload_resume", methods=["POST"])
def upload_resume():

    file = request.files.get("file")
    name = request.form.get("name")

    if not file or not name:
        return jsonify({"error": "Missing data"}), 400

    ext = file.filename.split('.')[-1]

    filename = f"Naukri_{name.replace(' ', '')}_{int(time.time())}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    file.save(filepath)

    return jsonify({
        "status": "success",
        "filename": filename,
        "path": filepath
    })
    
# =========================
# START SERVER
# =========================

if __name__ == "__main__":
    print("Download automation server running on http://127.0.0.1:5001")
    app.run(host="0.0.0.0", port=5001)