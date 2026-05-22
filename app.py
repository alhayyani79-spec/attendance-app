from flask import Flask, render_template, request, redirect, session
import os
import logging
import json
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from datetime import datetime

app = Flask(__name__)

# Use environment variable for secret key
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(16))

# Create data directory if it doesn't exist
os.makedirs("data", exist_ok=True)

# Gist backup configuration (optional but recommended for Render)
GIST_TOKEN = os.environ.get("GITHUB_GIST_TOKEN")  # Get from https://gist.github.com/
GIST_ID = os.environ.get("GIST_ID")  # Your backup Gist ID

# =========================
# BACKUP FUNCTIONS
# =========================

def backup_to_gist():
    """Backup all JSON files to GitHub Gist"""
    if not GIST_TOKEN or not GIST_ID:
        print("Gist backup not configured - skipping")
        return
    
    try:
        files = {}
        for filename in ["users.json", "activities.json", "attendance.json"]:
            with open(f"data/{filename}", "r") as f:
                files[filename] = {"content": f.read()}
        
        # Update Gist
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {
            "Authorization": f"token {GIST_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "files": files,
            "description": f"Attendance Backup - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        }
        
        response = requests.patch(url, headers=headers, json=data)
        if response.status_code == 200:
            print("Backup to Gist successful")
        else:
            print(f"Backup failed: {response.status_code}")
    except Exception as e:
        print(f"Backup error: {e}")

def restore_from_gist():
    """Restore JSON files from GitHub Gist"""
    if not GIST_TOKEN or not GIST_ID:
        print("Gist restore not configured - skipping")
        return False
    
    try:
        url = f"https://api.github.com/gists/{GIST_ID}"
        headers = {"Authorization": f"token {GIST_TOKEN}"}
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            gist_data = response.json()
            files = gist_data.get("files", {})
            
            for filename in ["users.json", "activities.json", "attendance.json"]:
                if filename in files:
                    content = files[filename]["content"]
                    with open(f"data/{filename}", "w") as f:
                        f.write(content)
            
            print("Restored from Gist backup")
            return True
    except Exception as e:
        print(f"Restore error: {e}")
    
    return False

# =========================
# LOAD JSON DATA WITH BACKUP
# =========================

def load_data():
    """Load data from JSON files, with auto-restore if missing"""
    
    # Check if files exist and are valid
    files_exist = all(os.path.exists(f"data/{f}") for f in ["users.json", "activities.json", "attendance.json"])
    
    if not files_exist:
        print("Data files missing, attempting restore from Gist...")
        if restore_from_gist():
            files_exist = True
    
    # Load or create default files
    try:
        with open("data/users.json", "r") as f:
            users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Default users with hashed passwords
        users = {
            "admin": generate_password_hash("1234"),
            "mohammad": generate_password_hash("1029"),
            "khaled": generate_password_hash("4321"),
            "hamad": generate_password_hash("5678")
        }
        save_users_only(users)
    
    try:
        with open("data/activities.json", "r") as f:
            activities = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        activities = {
            "national_day": {
                "title": "UAE National Day",
                "arabic": "اليوم الوطني الإماراتي",
                "description": "Family celebration with performances and food.",
                "date": "2 Dec 2024",
                "time": "5:00 PM - 8:00 PM",
                "location": "Main School Hall",
                "capacity": 30
            },
            "eid": {
                "title": "Eid Gathering",
                "arabic": "اجتماع الأسرة للعيد",
                "description": "Family gathering with food and activities.",
                "date": "First Day of Eid",
                "time": "6:00 PM - 9:00 PM",
                "location": "Family Majlis",
                "capacity": 40
            },
            "flag_day": {
                "title": "UAE Flag Day",
                "arabic": "يوم العلم",
                "description": "Flag ceremony and speeches.",
                "date": "3 Nov 2024",
                "time": "10:00 AM - 12:00 PM",
                "location": "School Yard",
                "capacity": 50
            },
            "memorial": {
                "title": "Commemoration Day",
                "arabic": "يوم الشهيد",
                "description": "Honoring UAE heroes.",
                "date": "30 Nov 2024",
                "time": "9:00 AM - 11:00 AM",
                "location": "Assembly Area",
                "capacity": 35
            }
        }
        save_activities_only(activities)
    
    try:
        with open("data/attendance.json", "r") as f:
            attendance = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        attendance = {
            "national_day": [],
            "eid": [],
            "flag_day": [],
            "memorial": []
        }
        save_attendance_only(attendance)
    
    return users, activities, attendance

def save_users_only(users):
    with open("data/users.json", "w") as f:
        json.dump(users, f, indent=4)

def save_activities_only(activities):
    with open("data/activities.json", "w") as f:
        json.dump(activities, f, indent=4)

def save_attendance_only(attendance):
    with open("data/attendance.json", "w") as f:
        json.dump(attendance, f, indent=4)

# =========================
# SAVE ALL DATA
# =========================

def save_all_data(users, activities, attendance):
    """Save all data to JSON files and optionally backup to Gist"""
    save_users_only(users)
    save_activities_only(activities)
    save_attendance_only(attendance)
    
    # Auto-backup to Gist if configured
    backup_to_gist()

# Load initial data
users, activities, attendance = load_data()

# =========================
# LOGGING
# =========================

logging.basicConfig(
    filename="attendance.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

# =========================
# LIVE ATTENDANCE
# =========================

def log_live_attendance():
    print("\033c", end="")
    print("\n=== LIVE ATTENDANCE ===\n")
    
    for key, users_list in attendance.items():
        if key in activities:
            print(activities[key]["title"])
            print("-" * 30)
            
            if users_list:
                for i, user in enumerate(users_list, 1):
                    print(f"{i}. {user}")
            else:
                print("No attendees")
            
            print()

# =========================
# HOME
# =========================

@app.route("/")
def home():
    return redirect("/login")

# =========================
# LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        if username in users and check_password_hash(users[username], password):
            session["user"] = username
            logging.info(f"User '{username}' logged in")
            return redirect("/dashboard")
        
        return render_template("login.html", error="Wrong login")
    
    return render_template("login.html")

# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    
    msg = session.pop("msg", None)
    
    return render_template(
        "dashboard.html",
        user=session["user"],
        activities=activities,
        attendance=attendance,
        msg=msg
    )

# =========================
# JOIN ACTIVITY
# =========================

@app.route("/join/<activity_id>")
def join(activity_id):
    if "user" not in session:
        return redirect("/login")
    
    user = session["user"]
    
    # ADMIN CANNOT JOIN
    if user == "admin":
        session["msg"] = "Admin cannot join activities."
        return redirect("/dashboard")
    
    if activity_id not in attendance:
        attendance[activity_id] = []
    
    if user not in attendance[activity_id]:
        if len(attendance[activity_id]) < activities[activity_id]["capacity"]:
            attendance[activity_id].append(user)
            save_all_data(users, activities, attendance)
            session["msg"] = "Joined successfully!"
            logging.info(f"User '{user}' joined activity '{activity_id}'")
    
    log_live_attendance()
    return redirect("/dashboard")

# =========================
# CANCEL ACTIVITY
# =========================

@app.route("/cancel/<activity_id>")
def cancel(activity_id):
    if "user" not in session:
        return redirect("/login")
    
    user = session["user"]
    
    if user in attendance.get(activity_id, []):
        attendance[activity_id].remove(user)
        save_all_data(users, activities, attendance)
        session["msg"] = "Cancelled!"
        logging.info(f"User '{user}' cancelled from activity '{activity_id}'")
    
    log_live_attendance()
    return redirect("/dashboard")

# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# =========================
# ADD ACCOUNT
# =========================

@app.route("/add_account", methods=["GET", "POST"])
def add_account():
    if "user" not in session:
        return redirect("/login")
    
    if session["user"] != "admin":
        return redirect("/dashboard")
    
    if request.method == "POST":
        new_username = request.form.get("username")
        new_password = request.form.get("password")
        
        if new_username in users:
            session["msg"] = "User already exists!"
            return redirect("/dashboard")
        
        if not new_username or not new_password:
            session["msg"] = "Invalid input!"
            return redirect("/dashboard")
        
        # Store hashed password
        users[new_username] = generate_password_hash(new_password)
        save_all_data(users, activities, attendance)
        
        session["msg"] = f"Account '{new_username}' created!"
        logging.info(f"Admin created account '{new_username}'")
        
        return redirect("/dashboard")
    
    return render_template("add_account.html")

# =========================
# REMOVE ACCOUNT
# =========================

@app.route("/remove_account", methods=["GET", "POST"])
def remove_account():
    if "user" not in session or session["user"] != "admin":
        return redirect("/dashboard")
    
    if request.method == "POST":
        username = request.form.get("username")
        
        if username == "admin":
            session["msg"] = "Cannot remove admin account!"
        elif username in users:
            del users[username]
            # Remove from all attendance lists
            for activity in attendance:
                if username in attendance[activity]:
                    attendance[activity].remove(username)
            save_all_data(users, activities, attendance)
            session["msg"] = f"Account '{username}' removed!"
            logging.info(f"Admin removed account '{username}'")
        else:
            session["msg"] = "User not found!"
        
        return redirect("/dashboard")
    
    # Filter out admin from list
    non_admin_users = [u for u in users.keys() if u != "admin"]
    return render_template("remove_account.html", users=non_admin_users)

# =========================
# ADD ACTIVITY
# =========================

@app.route("/add_activity", methods=["GET", "POST"])
def add_activity():
    if "user" not in session or session["user"] != "admin":
        return redirect("/dashboard")
    
    if request.method == "POST":
        activity_id = request.form.get("activity_id").lower().replace(" ", "_")
        
        if activity_id in activities:
            session["msg"] = "Activity ID already exists!"
            return redirect("/dashboard")
        
        activities[activity_id] = {
            "title": request.form.get("title"),
            "arabic": request.form.get("arabic"),
            "description": request.form.get("description"),
            "date": request.form.get("date"),
            "time": request.form.get("time"),
            "location": request.form.get("location"),
            "capacity": int(request.form.get("capacity"))
        }
        attendance[activity_id] = []
        save_all_data(users, activities, attendance)
        
        session["msg"] = f"Activity '{request.form.get('title')}' added!"
        logging.info(f"Admin added activity '{activity_id}'")
        
        return redirect("/dashboard")
    
    return render_template("add_activity.html")

# =========================
# REMOVE ACTIVITY
# =========================

@app.route("/remove_activity", methods=["GET", "POST"])
def remove_activity():
    if "user" not in session or session["user"] != "admin":
        return redirect("/dashboard")
    
    if request.method == "POST":
        activity_id = request.form.get("activity_id")
        
        if activity_id in activities:
            activity_title = activities[activity_id]["title"]
            del activities[activity_id]
            if activity_id in attendance:
                del attendance[activity_id]
            save_all_data(users, activities, attendance)
            session["msg"] = f"Activity '{activity_title}' removed!"
            logging.info(f"Admin removed activity '{activity_id}'")
        else:
            session["msg"] = "Activity not found!"
        
        return redirect("/dashboard")
    
    return render_template("remove_activity.html", activities=activities)

# =========================
# MANUAL BACKUP
# =========================

@app.route("/admin/backup")
def manual_backup():
    if session.get("user") != "admin":
        return "Unauthorized", 401
    
    backup_to_gist()
    session["msg"] = "Manual backup completed!"
    return redirect("/dashboard")

@app.route("/admin/restore")
def manual_restore():
    if session.get("user") != "admin":
        return "Unauthorized", 401
    
    if restore_from_gist():
        global users, activities, attendance
        users, activities, attendance = load_data()
        session["msg"] = "Data restored from backup!"
    else:
        session["msg"] = "Restore failed - check Gist configuration"
    
    return redirect("/dashboard")

# =========================
# RUN
# =========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5055))
    app.run(host="0.0.0.0", port=port)