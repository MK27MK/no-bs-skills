import httpx

TIMEOUT_SECONDS = 10


def fetch_stock(sku: str) -> int:
    response = httpx.get(f"https://inventory.internal/stock/{sku}", timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()["quantity"]
