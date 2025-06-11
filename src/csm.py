from typing import Optional
import httpx

from .config import CUBE_URL, CUBE_API_KEY

async def create_csm_session(image_urls: list) -> dict:
    url = f"{CUBE_URL}/v3/sessions/"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": CUBE_API_KEY
    }

    payload = {
        "type": "multiview_to_3d",
        "input": {
            "images": image_urls,
            "model": "sculpt",
            "settings": {
                "geometry_model": "base"
            }
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)

    response.raise_for_status()
    return response.json()


async def check_model_ready(session_id: str) -> Optional[dict]:
    url = f"{CUBE_URL}/v3/sessions/{session_id}"
    headers = {
        "Content-Type": "application/json",
        "x-api-key": CUBE_API_KEY
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)

    response.raise_for_status()
    data = response.json()

    # Check if the model is ready
    if data.get("status") == "complete":
        meshes = data.get("output", {}).get("meshes", [])
        if meshes:
            glb_url = meshes[0].get("data", {}).get("glb_url")
            if glb_url:
                return {"glb_url": glb_url}

    return None