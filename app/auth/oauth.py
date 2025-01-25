from fastapi import HTTPException
import aiohttp
from ..config import settings

async def verify_google_token(token: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
        ) as response:
            if response.status != 200:
                raise HTTPException(status_code=400, detail="Invalid Google token")
            user_data = await response.json()
            return user_data