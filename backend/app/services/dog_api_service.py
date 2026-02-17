# TODO: Enrique
import httpx
from app.core.config import settings

class DogAPIService:
    BASE_URL = "https://api.thedogapi.com/v1"

    async def get_breed_info(self, breed_name: str):
        async with httpx.AsyncClient() as client:
            # response = await client.get(..., headers={"x-api-key": settings.DOG_API_KEY})
            pass
