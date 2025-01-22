from requests import (get,
                      post,
                      __version__ as requests_version)

from json import loads, load
from os import getenv
import asyncio, aiohttp
import mysql.connector
from functools import wraps
from flask import current_app, request, jsonify, redirect, url_for

with open("webui.json", "r") as f:
    VERSION = load(f)["VERSION"]

INTERNAL_CACHE = {
    "SESSIONS": {}
}

DB_CONNECTION_INFO = {
    "host": getenv("MYSQL_HOST"),
    "user": getenv("MYSQL_USER"),
    "password": getenv("MYSQL_PASSWORD"),
    "database": getenv("MYSQL_DATABASE")
}
cnx = mysql.connector.connect(**DB_CONNECTION_INFO)

def makeRequestHeaders(token = None, bot = False):

    headers = {
        "User-Agent": "AlphaGameBot-WebUI (https://alphagamebot.alphagame.dev); curl/8.3.0; python-requests/%s" % requests_version,
        "Authorization": "NoType NoToken",
        "Accept": "application/json",
        "x-alphagamebot-webui-version": VERSION

    }
    if bot:
        headers["Authorization"] = "Bot %s" % getenv("BOT_TOKEN")
    else:
        headers["Authorization"] = "Bearer %s" % token
    return headers

def seperatedNumberByComma(number):
    return "{:,}".format(number)

def has_permission(permissions, permission) -> bool:
    return permissions & permission != 0

def get_user_by_id(user_id):
    r = get("https://discord.com/api/users/%s" % user_id, headers=makeRequestHeaders(bot = True))
    return r.json()

def get_user_info(access_token: str) -> dict:
    r = get("https://discord.com/api/users/@me", headers=makeRequestHeaders(access_token))
    return r.json()

def get_user_guilds(access_token):
    url = "https://discord.com/api/users/@me/guilds"
    response = get(url, headers=makeRequestHeaders(access_token))
    if response.status_code == 200:
        return response.json()
    else:
        current_app.logger.error("Failed to get user guilds: %s: %s" % (response.status_code, response.json()))
        return []

def get_user_guild_by_id(access_token, guild_id):
    url = f"https://discord.com/api/users/@me/guilds/{guild_id}/member"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    response = get(url, headers=headers)
    return response.json()

def get_guild_roles(guild_id):
    url = "https://discord.com/api/guilds/%s/roles" % guild_id
    return get(url, headers=makeRequestHeaders(bot = True)).json()

def user_has_administrator(token, guildid):
    guild = get_user_guild_by_id(token, guildid)
    roles = get_guild_roles(guildid)
    
    user_roles = guild.get("roles", [])
    if guild.get("code") == 10004:
        return False

    for role in roles:
        if role["id"] in user_roles and role.get("permissions") & 0x8:  # 0x8 is the bitwise value for ADMINISTRATOR
            return True
    return False

def get_guild_by_id(guild_id):
    url = "https://discord.com/api/guilds/%s" % guild_id
    headers = {
         "Authorization": "Bot %s" % getenv("BOT_TOKEN")
    }
    response = get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return response.json()
    
def mass_get_users_by_id_async(user_ids):
    url = "https://discord.com/api/users"
    headers = {
        "Authorization": "Bot %s" % getenv("BOT_TOKEN")
    }
    users = []
    # using aiohttp
    async def fetch(url, session, user_id, headers):
        complete_url = url + "/" + str(user_id)
        async with session.get(complete_url, headers=headers) as response:
            if response.status != 200:
                current_app.logger.error("Failed to fetch user %s: %s: %s" % (user_id, response.status, await response.json()))
            return await response.json()
    
    async def fetch_all(user_ids):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for user_id in user_ids:
                tasks.append(fetch(url, session, user_id, headers))
            return await asyncio.gather(*tasks)
    users = asyncio.run(fetch_all(user_ids))
    return users

def initialize_cache_for_session(session_id):
    logger = current_app.logger
    logger.debug("Initializing cache for session %s" % session_id)
    INTERNAL_CACHE["SESSIONS"][session_id] = {
        "user-profile-data": None
    }

def inject_token_user(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.cookies.get("access_token")
        session_id = request.cookies.get("session_id")

        if token is None or session_id is None:
            return redirect(url_for("auth_discord.sign_in"))
        
        if session_id not in INTERNAL_CACHE["SESSIONS"]:
            initialize_cache_for_session(session_id)

        cache = INTERNAL_CACHE["SESSIONS"][session_id]
        user = cache.get("user-profile-data")
        if user is None:
            user = get_user_info(token)
            cache["user-profile-data"] = user
        
        current_app.logger.debug("Injected user: (Username: %s, ID: %s)" % (user["username"], user["id"]))
        return func(token=token, user=user, *args, **kwargs)
    return wrapper