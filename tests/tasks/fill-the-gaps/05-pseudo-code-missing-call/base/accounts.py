from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    email: str
    last_login: datetime
    archived: bool = False
