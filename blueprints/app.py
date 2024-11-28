from flask import render_template, redirect, request, Response, Blueprint
from utility import get_user_info, get_user_guilds, cnx, has_permission, get_guild_by_id, seperatedNumberByComma, get_user_by_id
from os import getenv   
import logging

app = Blueprint("app", __name__)

def button2int(b):
    return 1 if b == "on" else 0

@app.before_request
def commit_db():
    cnx.ping(attempts = 4, reconnect = True)
    cnx.commit()

@app.before_request
def check_cookie():
    if not request.cookies.get("access_token"):
        return redirect("/auth/discord/signin")

@app.route("/")
def app_index():
    token = request.cookies.get("access_token")
    user = get_user_info(token)
    return render_template("app/app_home.html", user=user, client_id = getenv("DISCORD_CLIENT_ID"))

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

@app.route("/add-the-bot")
def app_add_the_bot():
    token = request.cookies.get("access_token")
    user = get_user_info(token)
    return render_template("app/add_the_bot.html", user=user)

@app.route("/logout")
def logout():
    r = redirect("/auth/discord/signin")
    r.set_cookie("access_token", "", expires=0)
    return r