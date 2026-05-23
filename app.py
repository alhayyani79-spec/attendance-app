from flask import Flask, render_template, request, redirect, session
import os
import logging
import json
import secrets
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(16))

# Create data directory
os.makedirs("data", exist_ok=True)

# =========================
# LOAD JSON DATA
# =========================

def load_data():
    # Load users
    try:
        with open("data/users.json", "r") as f:
            users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        users = {
            "admin": generate_password_hash("1234"),
            "mohammad": generate_password_hash("1029"),
            "khaled": generate_password_hash("4321"),
            "hamad": generate_password_hash("5678")
        }
        save_users_only(users)
    
    # Load activities
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
    
    # Load attendance
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

def save_all_data(users, activities, attendance):
    save_users_only(users)
    save_activities_only(activities)
    save_attendance_only(attendance)

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
# ADMIN REMOVE ATTENDEE
# =========================

@app.route("/admin/remove_attendee/<activity_id>/<username>")
def admin_remove_attendee(activity_id, username):
    if "user" not in session:
        return redirect("/login")
    
    if session["user"] != "admin":
        session["msg"] = "Unauthorized access!"
        return redirect("/dashboard")
    
    if activity_id not in attendance:
        session["msg"] = "Activity not found!"
        return redirect("/dashboard")
    
    if username in attendance[activity_id]:
        attendance[activity_id].remove(username)
        save_all_data(users, activities, attendance)
        session["msg"] = f"Removed '{username}' from {activities[activity_id]['title']}"
        logging.info(f"Admin removed '{username}' from activity '{activity_id}'")
    else:
        session["msg"] = f"'{username}' is not registered for this activity"
    
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
            for activity in attendance:
                if username in attendance[activity]:
                    attendance[activity].remove(username)
            save_all_data(users, activities, attendance)
            session["msg"] = f"Account '{username}' removed!"
            logging.info(f"Admin removed account '{username}'")
        else:
            session["msg"] = "User not found!"
        
        return redirect("/dashboard")
    
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
# EDIT ACTIVITY
# =========================

@app.route("/edit_activity/<activity_id>", methods=["GET", "POST"])
def edit_activity(activity_id):
    if "user" not in session or session["user"] != "admin":
        return redirect("/dashboard")
    
    if activity_id not in activities:
        session["msg"] = "Activity not found!"
        return redirect("/dashboard")
    
    if request.method == "POST":
        # Update activity with form data
        activities[activity_id] = {
            "title": request.form.get("title"),
            "arabic": request.form.get("arabic"),
            "description": request.form.get("description"),
            "date": request.form.get("date"),
            "time": request.form.get("time"),
            "location": request.form.get("location"),
            "capacity": int(request.form.get("capacity"))
        }
        save_all_data(users, activities, attendance)
        session["msg"] = f"Activity '{request.form.get('title')}' updated!"
        logging.info(f"Admin edited activity '{activity_id}'")
        return redirect("/dashboard")
    
    # GET request - show edit form with current data
    return render_template("edit_activity.html", activity=activities[activity_id], activity_id=activity_id)

# =========================
# DELETE ACTIVITY (from edit page)
# =========================

@app.route("/delete_activity/<activity_id>", methods=["POST"])
def delete_activity(activity_id):
    if "user" not in session or session["user"] != "admin":
        return redirect("/dashboard")
    
    if activity_id in activities:
        activity_title = activities[activity_id]["title"]
        del activities[activity_id]
        if activity_id in attendance:
            del attendance[activity_id]
        save_all_data(users, activities, attendance)
        session["msg"] = f"Activity '{activity_title}' deleted!"
        logging.info(f"Admin deleted activity '{activity_id}'")
    else:
        session["msg"] = "Activity not found!"
    
    return redirect("/dashboard")

# =========================
# REMOVE ACTIVITY (original - keep for compatibility)
# =========================

@app.route("/remove_activity", methods=["GET", "POST"])
def remove_activity_old():
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
# RUN
# =========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5055))
    app.run(host="0.0.0.0", port=port)