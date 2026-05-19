from flask import Flask, render_template, request, redirect, session
import os
import logging

app = Flask(__name__)
app.secret_key = "clean_login_system"

# USERS
users = {
    "admin": "1234",
    "mohammad": "1029",
    "khaled": "4321",
    "hamad": "5678",
}

# ACTIVITIES
activities = {
    "national_day": {
        "title": "UAE National Day",
        "arabic": "اليوم الوطني الإماراتي",
        "description": "Family celebration with performances and food.",
        "date": "2 Dec 2026",
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
        "date": "3 Nov 2026",
        "time": "10:00 AM - 12:00 PM",
        "location": "School Yard",
        "capacity": 50
    },

    "memorial": {
        "title": "Commemoration Day",
        "arabic": "يوم الشهيد",
        "description": "Honoring UAE heroes.",
        "date": "30 Nov 2026",
        "time": "9:00 AM - 11:00 AM",
        "location": "Assembly Area",
        "capacity": 35
    }
}

# ATTENDANCE
attendance = {
    "national_day": [],
    "eid": [],
    "flag_day": [],
    "memorial": []
}

# LOGGING
logging.basicConfig(
    filename="attendance.log",
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

def log_live_attendance():
    print("\033c", end="")
    print("\n=== LIVE ATTENDANCE ===\n")

    for key, users_list in attendance.items():
        print(activities[key]["title"])
        print("-" * 30)

        if users_list:
            for i, user in enumerate(users_list, 1):
                print(f"{i}. {user}")
        else:
            print("No attendees")

        print()

@app.route("/")
def home():
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in users and users[username] == password:
            session["user"] = username
            return redirect("/dashboard")

        return render_template("login.html", error="Wrong login")

    return render_template("login.html")


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


@app.route("/join/<activity_id>")
def join(activity_id):
    if "user" not in session:
        return redirect("/login")

    user = session["user"]

    if user not in attendance[activity_id]:
        if len(attendance[activity_id]) < activities[activity_id]["capacity"]:
            attendance[activity_id].append(user)
            session["msg"] = "Joined successfully!"

    log_live_attendance()
    return redirect("/dashboard")


@app.route("/cancel/<activity_id>")
def cancel(activity_id):
    if "user" not in session:
        return redirect("/login")

    user = session["user"]

    if user in attendance[activity_id]:
        attendance[activity_id].remove(user)
        session["msg"] = "Cancelled!"

    log_live_attendance()
    return redirect("/dashboard")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5055))
    app.run(host="0.0.0.0", port=port)