from flask import render_template, redirect, request, Response, Blueprint
from utility import get_user_info

app = Blueprint("app", __name__)

@app.before_request
def check_cookie():
    if not request.cookies.get("access_token"):
        return redirect("/auth/discord/signin?reason=noDiscordAccessCookie")

@app.route("/")
def app_index():
    token = request.cookies.get("access_token")
    user = get_user_info(token)
    return render_template("app-home.html", user=user)

@app.route("/dashboard")
def app_dashboard():
    token = request.cookies.get("access_token")
    user = get_user_info(token)
    return render_template("app-dashboard.html", user=user)

@app.route("/user")
def app_user():
    token = request.cookies.get("access_token")
    user = get_user_info(token)
    return render_template("user-information.html", user=user)

@app.route("/settings")
@app.route("/profile")
def not_implimented():
    token = request.cookies.get("access_token")
    user = get_user_info(token)
    return render_template("not-implimented.html", user=user)
@app.route("/logout")
def logout():
    r = redirect("/auth/discord/signin")
    r.set_cookie("access_token", "", expires=0)
    return r