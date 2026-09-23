from limiter import RateLimiter

limiter = RateLimiter(max_calls=5, per_seconds=1.0)


def handle(request: dict) -> dict:
    if not limiter.allow(request["client_id"]):
        return {"status": 429}
    return {"status": 200}
