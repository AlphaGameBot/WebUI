from flask import Flask, render_template, redirect, request, Response
import requests
from json import loads
from os import getenv
app = Flask(__name__)

@app.route('/')
def index():
    return render_template("main.html")

@app.route("/auth/discord/login")
def discord_login():
    return redirect("https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&response_type=code&scope=identify".format(
        CLIENT_ID=getenv("DISCORD_CLIENT_ID")
    ))

@app.route("/auth/discord/callback")
def discord_login_callback():
    args = request.args

    r = requests.post("https://discord.com/api/oauth2/token", data={
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
    print(j)
    r.set_cookie("access_token", j["access_token"])
    return r

@app.route("/app/")
def app_index():
    user_info = loads(requests.get("https://discord.com/api/users/@me", headers={
        "Authorization": "Bearer " + request.cookies.get("access_token")
    }).text)
    return render_template("login-success.html", json=user_info, user=user_info)