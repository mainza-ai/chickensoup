import logging
from fastapi import Header, HTTPException
from src.config import settings

logger = logging.getLogger("chickensoup.auth")


async def verify_api_key(x_api_key: str = Header(default=None)):
    """Verify API key for mutating endpoints. Skip if API_KEY is not configured (dev mode)."""
    if not settings.API_KEY:
        return  # Dev mode: no auth required
    if x_api_key != settings.API_KEY:
        logger.warning(
            f"Unauthorized API request with key: {x_api_key[:4]}..."
            if x_api_key
            else "Unauthorized API request: no key provided"
        )
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
