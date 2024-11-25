from requests import get
from json import loads
from os import getenv
import mysql.connector

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