from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    email: str
    last_login: datetime
    archived: bool = False


def archive_inactive(users: list[User], now: datetime) -> list[str]:
    # for each user not archived yet:
    #     if now - last_login > 90 days -> archived = True
    # log_archived(emails)
    # return the emails archived in this run, sorted
    ...
