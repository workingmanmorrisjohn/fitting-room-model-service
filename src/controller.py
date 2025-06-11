import asyncio
import httpx

from .image_preprocessing import remove_background, get_measurements
from .pocketbase import upload_to_pocketbase, upload_session_details, update_avatar_with_model, update_session_complete, get_image_url_of_avatar_source
from .csm import create_csm_session, check_model_ready
from .config import POCKETBASE_URL

# --- Main Avatar Creation Flow ---
async def create_entries(front_bytes: bytes, side_bytes: bytes, height: int):
    # Optionally do background removal here
    front_no_bg = await remove_background(front_bytes)
    side_no_bg = await remove_background(side_bytes)
    
    measurements = await get_measurements(front_no_bg, side_no_bg, height)
    print(f"Measurements: {measurements}")


    # 2. Upload to PocketBase
    avatar_object = await upload_to_pocketbase(front_no_bg, side_no_bg, height, measurements)
    print(f"Avatar uploaded with ID: {avatar_object}")
    
    image_urls = get_image_url_of_avatar_source(avatar_object["id"], avatar_object["front_view"], avatar_object["side_view"])
    
    # # 3. Create CSM session
    session = await create_csm_session(image_urls)
    session_id = session["_id"]
    
    print(f"Retrieved from csm: {session}")
    
    session_object = await upload_session_details(avatar_object["id"], session_id)
    print(f"Session created: {session_object}")


# --- Polling Task ---
async def poll_sessions():
    while True:
        print("Polling for model-ready sessions...")

        url = f"{POCKETBASE_URL}/api/collections/Sessions/records"
        params = {
            "filter": 'status="pending"'
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                records = response.json().get("items", [])

            pending_sessions = [
                {"session_id": rec["session_id"], "avatar_id": rec["avatar"]}
                for rec in records
            ]

            for session in pending_sessions:
                result = await check_model_ready(session["session_id"])
                if result:
                    print(f"Model ready for avatar {session['avatar_id']}")
                    await update_avatar_with_model(session["avatar_id"], result["glb_url"])
                    await update_session_complete(session["session_id"], result["glb_url"])
                else:
                    print(f"Model not ready for session {session['session_id']}")

        except Exception as e:
            print(f"Error while polling sessions: {e}")

        await asyncio.sleep(5)