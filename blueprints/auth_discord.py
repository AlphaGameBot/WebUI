from flask import Blueprint, render_template, redirect, request, Response
from requests import post, get
from json import loads
from os import getenv
from datetime import datetime, timedelta
from uuid import uuid4

auth_discord = Blueprint("auth_discord", __name__, template_folder="templates", static_folder="static")

@auth_discord.route("/signin")
def sign_in():
    """Not to be confused with /login.  This shows a more friendly interface to log in."""
    return render_template("login.html")

@auth_discord.route('/login')
def discord_login():
    scopes = [
        "identify",
        "guilds",
        "guilds.members.read"
    ]
    return redirect("https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&response_type=code&scope={SCOPES}".format(
        CLIENT_ID=getenv("DISCORD_CLIENT_ID"),
        SCOPES="+".join(scopes)
    ))

@auth_discord.route('/callback')
def discord_login_callback():
    args = request.args

    r = post("https://discord.com/api/oauth2/token", data={
        "client_id": getenv("DISCORD_CLIENT_ID"),
        "client_secret": getenv("DISCORD_CLIENT_SECRET"),
        "grant_type": "authorization_code",
        "code": args["code"],
        "redirect_uri": getenv("REDIRECT_URI"),
        "scope": "identify"
    })
    j = loads(r.content)
    if r.status_code != 200:
        reason = j.get("error_description", None)
        if not reason:
            reason = j.get("error", None)
        
        if not reason:
            print(j)
            reason = "No idea why it failed... :/"

        return Response("Error while logging in: %s" % reason, status=500)
    
    expires = datetime.now() + timedelta(seconds=j["expires_in"])

    r = redirect("/app/")
    r.set_cookie("access_token", j["access_token"], expires=expires)
    r.set_cookie("refresh_token", j["refresh_token"], expires=expires)
    r.set_cookie("session_id", str(uuid4()), expires=expires)
    return r
