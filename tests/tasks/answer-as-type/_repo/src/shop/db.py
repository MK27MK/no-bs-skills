from sqlalchemy import create_engine
from sqlalchemy.orm import Session


class ConnectionPool:
    def __init__(self, url: str) -> None:
        self.engine = create_engine(url, pool_size=5)

    def session(self) -> Session:
        return Session(self.engine)
