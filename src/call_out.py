import httpx
from io import BytesIO

from .config import REGISTER_URL, SIZE_URL

async def register(avatar_id: str):
    try:
        data = {
            "avatar_id": avatar_id
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                str(f'{REGISTER_URL}/register-and-fit'),
                data=data
            )
            response.raise_for_status()

    except Exception as e:
        print(f"Failed to update avatar {avatar_id} with model: {e}")


async def get_measurements(image_bytes: bytes) -> str:
    try:
        files = {
            'file': ("input_image.jpg", BytesIO(image_bytes))  # Only filename and file-like object
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                str(f'{SIZE_URL}/analyze-image'),
                files=files
            )
            response.raise_for_status()

        return response.json().get("size", "error")

    except Exception as e:
        print(f"Failed to get size recommendation: {e}")
