import json
import urllib.request

from retry import retry_on_error


@retry_on_error(3)
def fetch_user(user_id: int) -> dict:
    with urllib.request.urlopen(f"https://api.example.com/users/{user_id}") as response:
        return json.load(response)
