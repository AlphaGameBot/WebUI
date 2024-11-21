from flask import Blueprint, render_template, redirect, request, Response
from requests import post, get
from json import loads
from os import getenv

auth_discord = Blueprint("auth_discord", __name__, template_folder="templates", static_folder="static")

@auth_discord.route("/signin")
def sign_in():
    """Not to be confused with /login.  This shows a more friendly interface to log in."""
    return render_template("login.html")

@auth_discord.route('/login')
def discord_login():
    print("blueprin login")
    return redirect("https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&response_type=code&scope=identify".format(
        CLIENT_ID=getenv("DISCORD_CLIENT_ID")
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
        return Response("Error while logging in: %s" % j["error_description"] , status=500)
    
    
    r = redirect("/app/")
    r.set_cookie("access_token", j["access_token"])
    return r
