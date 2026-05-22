from flask import Flask, render_template, request, redirect, session
import os
import logging
import json

app = Flask(__name__)
app.secret_key = "clean_login_system"

# =========================
# LOAD JSON DATA
# =========================

def load_data():

    with open("data/users.json", "r") as f:
        users = json.load(f)

    with open("data/activities.json", "r") as f:
        activities = json.load(f)

    with open("data/attendance.json", "r") as f:
        attendance = json.load(f)

    return users, activities, attendance


# =========================
# SAVE JSON DATA
# =========================

def save_data():

    with open("data/users.json", "w") as f:
        json.dump(users, f, indent=4)

    with open("data/activities.json", "w") as f:
        json.dump(activities, f, indent=4)

    with open("data/attendance.json", "w") as f:
        json.dump(attendance, f, indent=4)


# LOAD EVERYTHING
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

        if username in users and users[username] == password:

            session["user"] = username

            return redirect("/dashboard")

        return render_template(
            "login.html",
            error="Wrong login"
        )

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

    if user not in attendance[activity_id]:

        if len(attendance[activity_id]) < activities[activity_id]["capacity"]:

            attendance[activity_id].append(user)

            # SAVE
            save_data()

            session["msg"] = "Joined successfully!"

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

    if user in attendance[activity_id]:

        attendance[activity_id].remove(user)

        # SAVE
        save_data()

        session["msg"] = "Cancelled!"

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
# RUN
# =========================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5055))

    app.run(
        host="0.0.0.0",
        port=port
    )