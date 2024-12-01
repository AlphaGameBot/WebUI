from flask import Blueprint, render_template, request, redirect
from utility import (
    get_user_info,
    cnx,
    get_user_guilds,
    has_permission,
    get_guild_by_id,
    get_user_guild_by_id,
    user_has_administrator
)

app_admin = Blueprint("app_admin", __name__)

def button2int(b):
    return 1 if b == "on" else 0

def userHasPermissionToServer(guild):
    return has_permission(guild["permissions"], 8)

@app_admin.route("/")
def app_admin_index():
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

@app_admin.route("/guild/<int:guildid>")
def app_guild(guildid):
    token = request.cookies.get("access_token")
    user = get_user_info(token)
    if not user_has_administrator(token, guildid):
        return render_template("simple-message.html", title="No Permission", message="You do not have permission to do this. (Nice try, though!)", user=user)
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

@app_admin.route("/guild/<int:guildid>/updateSettings", methods=["POST"])
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
    return redirect("/app/admin/guild/%s/settingsUpdated" % guildid)

@app_admin.route("/guild/<int:guildid>/settingsUpdated", methods=["GET"])
def app_guild_updated(guildid):
    token = request.cookies.get("access_token")
    user = get_user_info(token)
    guild = get_guild_by_id(guildid)

    return render_template("app/admin_guild_updated.html", user=user, guild=guild)