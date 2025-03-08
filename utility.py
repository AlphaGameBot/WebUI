from requests import (get,
                      post,
                      __version__ as requests_version)

from json import loads, load
from os import getenv
import asyncio, aiohttp
import mysql.connector
from functools import wraps
from flask import current_app, request, jsonify, redirect, url_for
import time

with open("webui.json", "r") as f:
    VERSION = load(f)["VERSION"]

INTERNAL_CACHE = {
    "SESSIONS": {},
    "USERS": {}, # Basically just a Discord user data cache with the item in the dict "_agb_cache_expires" being the time it expires and needs to be refreshed
    "GUILDS": {} # Same as above but for guilds
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
    
    # Check cache first
    current_time = time.time()
    cached_users = []
    users_to_fetch = []
    
    for user_id in user_ids:
        user_id_str = str(user_id)
        if user_id_str in INTERNAL_CACHE["USERS"] and INTERNAL_CACHE["USERS"][user_id_str].get("_agb_cache_expires", 0) > current_time:
            # Cache hit
            cached_users.append(INTERNAL_CACHE["USERS"][user_id_str])
        else:
            # Cache miss or expired
            users_to_fetch.append(user_id)
    
    # If all users are in cache, return them immediately
    if not users_to_fetch:
        return cached_users
    
    # Otherwise, fetch the missing users
    async def fetch(url, session, user_id, headers):
        complete_url = url + "/" + str(user_id)
        async with session.get(complete_url, headers=headers) as response:
            if response.status != 200:
                j = await response.json()
                code = response.status
                current_app.logger.error("Failed to fetch user %s: %s: %s" % (user_id, response.status, j))
                if code == 429:
                    current_app.logger.error("oh fuck we're getting ratelimited!  Waiting %s seconds to make Discord happy", j["retry_after"])
                    await asyncio.sleep(j["retry_after"])
                    return await fetch(url, session, user_id, headers)
            return await response.json()
    
    async def fetch_all(user_ids):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for user_id in user_ids:
                tasks.append(fetch(url, session, user_id, headers))
            fetched_users = await asyncio.gather(*tasks)
            
            # Cache the fetched users
            for user_data in fetched_users:
                if "id" in user_data:
                    user_id = user_data["id"]
                    # Add expiration timestamp (5 minutes)
                    user_data["_agb_cache_expires"] = time.time() + 300  # 5 minutes = 300 seconds
                    INTERNAL_CACHE["USERS"][user_id] = user_data
            
            return fetched_users
    
    # Only fetch users not in cache
    fetched_users = []
    if users_to_fetch:
        fetched_users = asyncio.run(fetch_all(users_to_fetch))
    
    # Combine cached and fetched users
    all_users = cached_users + fetched_users
    return all_users

def mass_get_guilds_by_id_async(guild_ids: list[int]) -> dict[int, dict]:
    url = "https://discord.com/api/guilds"
    headers = {
        "Authorization": "Bot %s" % getenv("BOT_TOKEN")
    }
    
    # Check cache first
    current_time = time.time()
    result_dict = {}
    guilds_to_fetch = []
    
    for guild_id in guild_ids:
        guild_id_str = str(guild_id)
        if guild_id_str in INTERNAL_CACHE["GUILDS"] and INTERNAL_CACHE["GUILDS"][guild_id_str].get("_agb_cache_expires", 0) > current_time:
            # Cache hit
            guild_data = INTERNAL_CACHE["GUILDS"][guild_id_str]
            result_dict[int(guild_id)] = guild_data
        else:
            # Cache miss or expired
            guilds_to_fetch.append(guild_id)
    
    # If all guilds are in cache, return them immediately
    if not guilds_to_fetch:
        return result_dict
    
    async def fetch(url, session, guild_id, headers):
        complete_url = url + "/" + str(guild_id)
        async with session.get(complete_url, headers=headers) as response:
            if response.status != 200:
                j = await response.json()
                code = response.status
                current_app.logger.error("Failed to fetch guild %s: %s: %s" % (guild_id, response.status, j))
                if code == 429:
                    current_app.logger.error("Rate limited! Waiting %s seconds to make Discord happy", j["retry_after"])
                    await asyncio.sleep(j["retry_after"])
                    return await fetch(url, session, guild_id, headers)
            return await response.json()
    
    async def fetch_all(guild_ids):
        async with aiohttp.ClientSession() as session:
            tasks = []
            for guild_id in guild_ids:
                tasks.append(fetch(url, session, guild_id, headers))
            results = await asyncio.gather(*tasks)
            
            # Convert to dictionary with guild_id as key and cache the results
            guilds_dict = {}
            for i, guild_data in enumerate(results):
                if "id" in guild_data:
                    guild_id = guild_data["id"]
                    # Add expiration timestamp (5 minutes)
                    guild_data["_agb_cache_expires"] = time.time() + 300  # 5 minutes = 300 seconds
                    INTERNAL_CACHE["GUILDS"][guild_id] = guild_data
                    guilds_dict[int(guild_id)] = guild_data
                else:
                    current_app.logger.warning(f"Could not fetch guild data for ID {guild_ids[i]}")
            return guilds_dict
    
    # Only fetch guilds not in cache
    if guilds_to_fetch:
        fetched_guilds = asyncio.run(fetch_all(guilds_to_fetch))
        # Merge with cached results
        result_dict.update(fetched_guilds)
    
    return result_dict

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