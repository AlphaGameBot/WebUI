from requests import get
from json import loads
from os import getenv
import asyncio, aiohttp
import mysql.connector
from flask import current_app

DB_CONNECTION_INFO = {
    "host": getenv("MYSQL_HOST"),
    "user": getenv("MYSQL_USER"),
    "password": getenv("MYSQL_PASSWORD"),
    "database": getenv("MYSQL_DATABASE")
}
cnx = mysql.connector.connect(**DB_CONNECTION_INFO)

def seperatedNumberByComma(number):
    return "{:,}".format(number)
def has_permission(permissions, permission):
    return permissions & permission != 0

def get_user_by_id(user_id):
    r = get("https://discord.com/api/users/%s" % user_id, headers={
        "Authorization": "Bot %s" % getenv("BOT_TOKEN")
    })
    return loads(r.content)

def get_user_info(access_token: str) -> dict:
    r = get("https://discord.com/api/users/@me", headers={
        "Authorization": "Bearer %s" % access_token
    })
    return loads(r.content)

def get_user_guilds(access_token):
        url = "https://discord.com/api/users/@me/guilds"
        headers = {
            "Authorization": "Bearer %s" % access_token
        }
        response = get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            return []

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
