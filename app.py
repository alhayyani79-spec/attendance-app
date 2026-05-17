from flask import Flask, render_template, request, redirect, session
import os

app = Flask(__name__)
app.secret_key = "clean_login_system"

# USERS
users = {
    "admin": "1234",
    "mohammad": "1029",
    "khaled": "4321",
    "hamad": "5678",
}

# ACTIVITIES (safe IDs + display names)
activities = {
    "national_day": "UAE National Day, يوم الوطني الاماراتي",
    "eid": "Eid Gathering, اجتماع الاسره فلعيد",
    "flag_day": "UAE Flag day, يوم العلم",
    "memorial": "Commemoration Day, يوم الشهيد"
}

# ATTENDANCE STORAGE
attendance = {
    "national_day": [],
    "eid": [],
    "flag_day": [],
    "memorial": []
}

# =========================
# LIVE TERMINAL FUNCTION
# =========================
def print_live_attendance():
    print("\033c", end="")  # clear terminal

    print("\n========== LIVE ATTENDANCE SNAPSHOT ==========\n")

    for key, users_list in attendance.items():
        print(f"📌 {activities[key]}")
        print("-" * 45)

        if users_list:
            for i, user in enumerate(users_list, 1):
                print(f"{i}. {user}")
        else:
            print("No attendees yet")

        print()

    print("==============================================\n")


# =========================
# ROUTES
# =========================

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

        return render_template("login.html", error="Wrong username or password")

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
        attendance[activity_id].append(user)
        session["msg"] = f"Attended {activities[activity_id]}!"

    print_live_attendance()

    return redirect("/dashboard")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# =========================
# RUN (DEPLOYMENT READY)
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5055))
    app.run(host="0.0.0.0", port=port)