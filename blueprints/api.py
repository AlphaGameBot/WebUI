from flask import Blueprint, render_template, redirect, request, Response, current_app
from requests import post, get
from utility import cnx
from requests import post
from os import getenv

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

@api.route("/discord", methods=["POST"])
def discord():
    # https://discord.com/developers/docs/events/webhook-events#event-types
    data = request.json or {}
    current_app.logger.info(f"Received Discord webhook: {data}")
    # the documentation is a bit misleading, it says `type` is an integer but it is actually a string in the payload
    
    # PING event
    if data.get("type") == 0:
        return "", 204 # To properly acknowledge a `PING` payload, return a `204` response with no body
    
    assert data.get("type") == 1, "Unknown event type received from Discord webhook"

    event = data.get("event", {})

    assert event.get("type", None) != None, "Event type is missing from the Discord webhook payload"

    wh_url = getenv("WEBHOOK")
    assert wh_url is str and len(wh_url) > 0, "WEBHOOK environment variable is not set or is empty"

    if event["type"] == "APPLICATION_AUTHORIZED":
        data = "# Application Authorized\n\n"
        data += f"**User:** `{event['data']['user']['username']}` (ID: {event['data']['user']['id']})\n"
        if event["data"].get("guild", None):
            data += f"**Guild:** `{event['data']['guild']['name']}` (ID: {event['data']['guild']['id']})\n"
        
        post(wh_url, json={"content": data})

    return {"message": "Discord webhook received"}, 200
