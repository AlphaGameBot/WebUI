from flask import Flask, render_template, redirect, request, Response
from flask_font_awesome import FontAwesome
from flask_resize import Resize
import requests
import logging
from json import loads
from os import getenv
from utility import get_user_info
from blueprints.auth_discord import auth_discord
from blueprints.app import app as app_bp
from blueprints.app_stats import app_stats
from blueprints.app_admin import app_admin
from blueprints.api import api
logging.basicConfig(format="%(message)s")

app = Flask(__name__, static_url_path='/static')
# flask_resize config
app.config['RESIZE_URL'] = '/static/img'
app.config['RESIZE_ROOT'] = 'static/img'
fa = FontAwesome(app)
resize = Resize(app)

app.register_blueprint(auth_discord, url_prefix="/auth/discord")
app.register_blueprint(app_bp, url_prefix="/app")
app.register_blueprint(app_stats, url_prefix="/app/stats/")
app.register_blueprint(app_admin, url_prefix="/app/admin/")
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

@app.errorhandler(500)
def internal_server_error(e):
    user = None
    if request.cookies.get("access_token"):
        user = get_user_info(request.cookies.get("access_token"))

    return render_template("simple-message.html", title="500 Internal Server Error", 
                           message="The server encountered an error and cannot complete the request.", user=user), 500

@app.errorhandler(403)
def forbidden(e):
    user = None
    if request.cookies.get("access_token"):
        user = get_user_info(request.cookies.get("access_token"))

    return render_template("simple-message.html", title="403 Forbidden", 
                           message="You do not have permission to access this resource.", user=user), 403

@app.errorhandler(401)
def unauthorized(e):
    user = None
    if request.cookies.get("access_token"):
        user = get_user_info(request.cookies.get("access_token"))

    return render_template("simple-message.html", title="401 Unauthorized", 
                           message="You must be logged in to access this resource.", user=user), 401

@app.errorhandler(400)
def bad_request(e):
    user = None
    if request.cookies.get("access_token"):
        user = get_user_info(request.cookies.get("access_token"))

    return render_template("simple-message.html", title="400 Bad Request", 
                           message="The server could not understand the request.", user=user), 400

@app.route("/favicon.ico")
def favicon():
    return app.send_static_file("icon.png")
