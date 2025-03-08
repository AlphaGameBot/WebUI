from flask import Blueprint, render_template, redirect, request, Response, current_app
from requests import post, get
from utility import cnx, INTERNAL_CACHE

api = Blueprint("api", __name__, template_folder="templates", static_folder="static")

@api.route("/stats/global/<int:user_id>")
def global_stats(user_id):
    cursor = cnx.cursor()
    cursor.execute("SELECT messages_sent, commands_ran FROM user_stats WHERE userid = %s", [user_id])
    user = cursor.fetchone()
    if user is None:
        return {
            "error": "User not found!"
        }, 404
    messages_sent, commands_ran = user
    
    return {
        "userid": user_id,
        "messages_sent": messages_sent,
        "commands_ran": commands_ran
    }

@api.route("/internalCache")
def internal_cache():
    if not current_app.debug:
        return {
            "error": "This endpoint is only available in debug mode!"
        }, 403
    return INTERNAL_CACHE