from typing import Optional
import httpx

from .config import CUBE_URL, CUBE_API_KEY

import json

async def create_csm_session(image_urls: list, retries=3, delay=5) -> dict:
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

    timeout = httpx.Timeout(connect=10.0, read=90.0, write=10.0, pool=5.0)

    for attempt in range(1, retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

        except httpx.ReadTimeout as e:
            print(f"⚠️ Timeout on attempt {attempt}/{retries}")
            if attempt == retries:
                raise
            await asyncio.sleep(delay)


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
            obj_url = meshes[0].get("data", {}).get("obj_url")

            output = {}

            if glb_url:
                output["glb_url"] = glb_url

            if obj_url:
                output["obj_url"] = obj_url

            return output

    return None