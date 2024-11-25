from flask import render_template, redirect, request, Response, Blueprint
from utility import get_user_info, get_user_guilds, cnx, has_permission, get_guild_by_id, seperatedNumberByComma
import logging

app = Blueprint("app", __name__)

def button2int(b):
    return 1 if b == "on" else 0

@app.before_request
def commit_db():
    cnx.commit()
@app.before_request
def check_cookie():
    if not request.cookies.get("access_token"):
        return redirect("/auth/discord/signin?reason=noDiscordAccessCookie")

@app.route("/")
def app_index():
    token = request.cookies.get("access_token")
    user = get_user_info(token)
    return render_template("app/home.html", user=user)

@app.route("/dashboard")
def app_dashboard():
    token = request.cookies.get("access_token")
    user = get_user_info(token)
    return render_template("app/dashboard.html", user=user)

@app.route("/user")
def app_user():
    token = request.cookies.get("access_token")
    user = get_user_info(token)
    return render_template("user-information.html", user=user)

@app.route("/profile")
def app_profile():
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

@app.route("/stats/guild/<int:guildid>")
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
@app.route("/settings")
def not_implimented():
    token = request.cookies.get("access_token")
    user = get_user_info(token)
    return render_template("not-implimented.html", user=user)

@app.route("/admin")
def app_admin():
    token = request.cookies.get("access_token")
    user = get_user_info(token)
    cursor = cnx.cursor()
    cursor.execute("SELECT guildid FROM guild_settings")
    agb_guilds_tp = cursor.fetchall()
    agb_guilds = []
    for i in agb_guilds_tp:
        agb_guilds.append(i[0])
    admin_guilds = []
    guilds = get_user_guilds(token)
    for guild in guilds:
        gid = int(guild["id"])
        
        if gid not in agb_guilds: continue
        if has_permission(guild["permissions"], 8):
            admin_guilds.append(guild)
        
    return render_template("app/admin.html", user=user, guilds=admin_guilds)

@app.route("/admin/guild/<int:guildid>")
def app_guild(guildid):
    token = request.cookies.get("access_token")
    user = get_user_info(token)
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM guild_settings WHERE guildid=%s", (guildid,))
    guilddb = cursor.fetchone()
    if not guilddb:
        return render_template("simple-message.html", title="Unknown Guild", message="AlphaGameBot doesn't know that guild... Is AlphaGameBot in that server?", user=user)
    leveling = guilddb[2]
    guild = get_guild_by_id(guildid)
    
    if guild.get("code") == 10004:
        return render_template("simple-message.html", user=user, title="Guild Not Found", message="AlphaGameBot can't find the requested guild.  Either it doesn't exist (it happens to the best of us!), or AlphaGameBot is not in that guild, yet.")
    return render_template("app/admin_guild.html", user=user, guild=guild, guilddb=guilddb, leveling=leveling)

@app.route("/admin/guild/<int:guildid>/updateSettings", methods=["POST"])
def app_guild_update(guildid):
    token = request.cookies.get("access_token")
    user = get_user_info(token)
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM guild_settings WHERE guildid=%s", (guildid,))
    guilddb = cursor.fetchone()
    if not guilddb:
        return render_template("simple-message.html", title="Unknown Guild", message="AlphaGameBot doesn't know that guild... Is AlphaGameBot in that server?", user=user)
    
    guild = [g for g in get_user_guilds(token) if int(g["id"]) == guildid][0]
    
    if guild.get("code") == 10004:
        return render_template("simple-message.html", user=user, title="Guild Not Found", message="AlphaGameBot can't find the requested guild.  Either it doesn't exist (it happens to the best of us!), or AlphaGameBot is not in that guild, yet.")
    
    if not has_permission(guild["permissions"], 8):
        return render_template("simple-message.html", user=user, title="No Permission", message="You do not have permission to do this.")
    
    print(request.form.get("leveling_enabled"), button2int(request.form.get("leveling_enabled")))
    cursor.execute("UPDATE guild_settings SET leveling_enabled=%s WHERE guildid=%s", (button2int(request.form.get("leveling_enabled")), guildid))
    cnx.commit()
    cursor.close()
    return redirect("/app/admin/guild/" + str(guildid) + "?updatedSettings=1")

@app.route("/about")
def app_about():
    token = request.cookies.get("access_token")
    user = get_user_info(token)
    return render_template("app/about.html", user=user)

@app.route("/logout")
def logout():
    r = redirect("/auth/discord/signin")
    r.set_cookie("access_token", "", expires=0)
    return r