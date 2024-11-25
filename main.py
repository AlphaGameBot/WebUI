from flask import Flask, render_template, redirect, request, Response
import requests
import logging
from json import loads
from os import getenv
from utility import get_user_info
from blueprints.auth_discord import auth_discord
from blueprints.app import app as app_bp

app = Flask(__name__, static_url_path='/static')
app.register_blueprint(auth_discord, url_prefix="/auth/discord")
app.register_blueprint(app_bp, url_prefix="/app")

if app.debug:
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)
@app.route('/')
def index():
    return redirect("/app/")

@app.route("/helloworld")
def hello_world():
    return "<h1>Hello, World!</h1>"

@app.errorhandler(404)
def page_not_found(e):
    user = None
    if request.cookies.get("access_token"):
        user = get_user_info(request.cookies.get("access_token"))

    return render_template("404.html", user=user), 404

@app.route("/favicon.ico")
def favicon():
    return app.send_static_file("icon.png")

if __name__ == "__main__":
    app.run("0.0.0.0", 5000)