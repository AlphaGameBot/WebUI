from os import getenv
from requests import (
    get as http_get,
    post as http_post
)
from json import dumps
from sys import exit as _exit
healthcheck_url = "https://alphagamebot.alphagame.dev/healthcheck"
def webhook_send(message):
    webhook = getenv("JENKINS_DISCORD_WEBHOOK")
    r = http_post(webhook, {
        "content": message
    })
    print("Webhook sent!  Status code:", r.status_code)

healthcheck = http_get(healthcheck_url)

if healthcheck.status_code != 200:
    webhook_send(f"""# :warning: **AlphaGameBot WebUI healthcheck failed!**
The healthcheck endpoint returned a non-200 status code. This is a critical error and should be investigated immediately.

* **Status Code:** `{healthcheck.status_code}`
* **Healthcheck URL:** `{healthcheck_url}`""")
    _exit(1)
else:
    webhook_send(f""":white_check_mark: **AlphaGameBot WebUI healthcheck passed!**
```json
{dumps(healthcheck.json(), indent=4)}
```""")
    _exit(0)
