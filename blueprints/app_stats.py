from flask import request, Blueprint, render_template, redirect, current_app
from utility import (
    cnx,
    seperatedNumberByComma,
    get_user_by_id,
    get_user_info,
    get_user_guilds,
    get_guild_by_id,
    mass_get_users_by_id_async
)

app_stats = Blueprint("app_stats", __name__)

@app_stats.before_request
def check_cookie():
    if not request.cookies.get("access_token"):
        return redirect("/auth/discord/signin")
    cnx.ping(attempts = 4, reconnect = True)
    cnx.commit()

@app_stats.route("/")
def app_profile():
    current_app.logger.debug("app_profile ok")
    token = request.cookies.get("access_token")
    user = get_user_info(token)

    all_guilds = get_user_guilds(token)
    guilds = []
    cursor = cnx.cursor()
    cursor.execute("SELECT guildid FROM guild_settings")
    known_guilds = [id[0] for id in cursor.fetchall()]
    for guild in all_guilds:
        if int(guild["id"]) in known_guilds:
            guilds.append(guild)

    cursor = cnx.cursor()
    cursor.execute("SELECT messages_sent FROM user_stats WHERE userid=%s", (user["id"],))
    messages_sent = cursor.fetchone()[0]
    return render_template("app/user_profile.html", user=user, messages_sent=seperatedNumberByComma(messages_sent), guilds=guilds)

@app_stats.route("/guild/<int:guildid>")
def app_guild_stats(guildid):
    token = request.cookies.get("access_token")
    user = get_user_info(token)
    cursor = cnx.cursor()
    cursor.execute("SELECT leveling_enabled FROM guild_settings WHERE guildid=%s", (guildid,))
    guilddb = cursor.fetchone()[0]
    if not guilddb:
        return render_template("simple-message.html", title="Unknown Guild", message="AlphaGameBot doesn't know that guild... Is AlphaGameBot in that server, and is leveling enabled?", user=user)
    guild = get_guild_by_id(guildid)
    
    if guild.get("code") == 10004:
        return render_template("simple-message.html", user=user, title="Guild Not Found", message="AlphaGameBot can't find the requested guild.  Either it doesn't exist (it happens to the best of us!), or AlphaGameBot is not in that guild, yet.")
    
    cursor.execute("SELECT user_level, points, messages_sent, commands_ran FROM guild_user_stats WHERE userid = %s AND guildid = %s", (user["id"], guildid))
    level, points, messages_sent, commands_ran = cursor.fetchone()

    return render_template("app/guild_user_stats.html", user=user, guild=guild, level=level, points=points, messages_sent=messages_sent, commands_ran=commands_ran)

@app_stats.route("/leaderboard")
def app_leaderboard():
    token = request.cookies.get("access_token")
    user = get_user_info(token)

    user["id"] = int(user["id"]) # discord id is a string, but we need it as an int
    cursor = cnx.cursor()
    # get list with 10 highest levels
    cursor.execute("SELECT userid FROM guild_user_stats ORDER BY (messages_sent+commands_ran*5) DESC LIMIT 10")
    users_db = cursor.fetchall()
    # 1. get the top 10 user (IDs)
    top10userids = [uid[0] for uid in users_db]
    
    # 2. get the user info for each user async
    users = mass_get_users_by_id_async(top10userids)

    # get the stats for the current logged-in user
    cursor.execute("SELECT messages_sent, commands_ran FROM user_stats WHERE userid=%s", (user["id"],))
    re = cursor.fetchone()
    if re is None:
        messages_sent = 0
        commands_ran = 0
        points = 0
    else:
        messages_sent, commands_ran = re
        points = messages_sent + commands_ran * 5
    user["statistics"] = {
        "messages_sent": messages_sent,
        "commands_ran": commands_ran,
        "points": points
    }

    for leaderboard_user in users:
        cursor.execute("SELECT messages_sent, commands_ran FROM user_stats WHERE userid=%s", (leaderboard_user["id"],))
        re = cursor.fetchone()
        if re is None:
            messages_sent = 0
            commands_ran = 0
        else:
            messages_sent, commands_ran = re
        info = {
            "messages_sent": messages_sent,
            "commands_ran": commands_ran,
            "points": messages_sent + commands_ran * 5
        }
        leaderboard_user["statistics"] = info
    
    cursor.execute("SELECT userid FROM user_stats ORDER BY messages_sent+commands_ran*5 DESC")
    all_users = cursor.fetchall()
    all_user_ids = [uid[0] for uid in all_users] # list[int]

    users.sort(key=lambda x: x["statistics"]["points"], reverse=True)
    user_ids = [int(_user["id"]) for _user in users]
    user_place = all_user_ids.index(user["id"]) + 1
    total_user_count = seperatedNumberByComma(len(all_user_ids))
    
    user_place = all_user_ids.index(int(user["id"])) + 1
    return render_template("app/stats_leaderboard.html", user=user, users=users, current_user_place=user_place, total_user_count=total_user_count)

@app_stats.route("/user/<int:userid>")
def app_user_stats(userid):
    token = request.cookies.get("access_token")
    user = get_user_info(token)
    showing_user = get_user_by_id(userid)
    cursor = cnx.cursor()
    cursor.execute("SELECT messages_sent, commands_ran FROM user_stats WHERE userid = %s", (userid,))
    messages_sent, commands_ran = cursor.fetchone()
    return render_template("app/user_stats_page.html", user=user, showing_user=showing_user, messages_sent=messages_sent, commands_ran=commands_ran)