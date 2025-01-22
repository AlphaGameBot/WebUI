from flask import Blueprint, render_template, redirect, request, Response
from requests import post, get
from utility import cnx

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