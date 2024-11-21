from flask import Flask, render_template, redirect, request, Response
import requests
from json import loads
from os import getenv
from utility import get_user_info
from blueprints.auth_discord import auth_discord
from blueprints.app import app as app_bp

app = Flask(__name__)
app.register_blueprint(auth_discord, url_prefix="/auth/discord")
app.register_blueprint(app_bp, url_prefix="/app")

@app.route('/')
def index():
    return redirect("/app/")

@app.errorhandler(404)
def page_not_found(e):
    user = None
    if request.cookies.get("access_token"):
        user = get_user_info(request.cookies.get("access_token"))

    return render_template("404.html", user=user), 404
if __name__ == "__main__":
    app.run("0.0.0.0", 5000)