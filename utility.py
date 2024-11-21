from requests import get
from json import loads

def get_user_info(access_token: str) -> dict:
    r = get("https://discord.com/api/users/@me", headers={
        "Authorization": "Bearer %s" % access_token
    })
    return loads(r.content)
