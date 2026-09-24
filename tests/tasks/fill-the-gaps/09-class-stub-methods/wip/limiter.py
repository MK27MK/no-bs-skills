import time


class RateLimiter:
    def __init__(self, max_calls: int, per_seconds: float) -> None:
        ...

    def allow(self, client_id: str) -> bool:
        ...
