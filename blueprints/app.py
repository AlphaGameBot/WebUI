from flask import render_template, redirect, request, Response, Blueprint
from utility import get_user_info, get_user_guilds, cnx, has_permission, get_guild_by_id, seperatedNumberByComma, get_user_by_id, inject_token_user
from os import getenv   
import logging

app = Blueprint("app", __name__)

@app.before_request
def commit_db():
    cnx.ping(attempts = 4, reconnect = True)
    cnx.commit()

@app.before_request
def check_cookie():
    if not request.cookies.get("access_token"):
        return redirect("/auth/discord/signin")

@app.route("/")
@inject_token_user
def app_index(token, user):
    return render_template("app/app_home.html", user=user, client_id = getenv("DISCORD_CLIENT_ID"))

@app.route("/dashboard")
@inject_token_user
def app_dashboard(token, user):
    return render_template("app/dashboard.html", user=user)

@app.route("/user")
@inject_token_user
def app_user(token, user):
    return render_template("user-information.html", user=user)

@app.route("/settings")
@inject_token_user
def not_implimented(token, user):
    return render_template("not-implimented.html", user=user)

@app.route("/about")
@inject_token_user
def app_about(token, user):
    return render_template("app/about.html", user=user)

@app.route("/add-the-bot")
@inject_token_user
def app_add_the_bot(token, user):
    return render_template("app/add_the_bot.html", user=user)

@app.route("/logout")
def logout():
    r = redirect("/auth/discord/signin")
    r.set_cookie("access_token", "", expires=0)
    return r