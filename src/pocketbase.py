import httpx

from .config import POCKETBASE_URL

avatar_endpoint = POCKETBASE_URL + "/api/collections/Avatars/records"
session_endpoint = POCKETBASE_URL + "/api/collections/Sessions/records"

async def upload_to_pocketbase(front: bytes, side: bytes, height: int, measurements: dict) -> dict:
    data = {
        "height": round(height, 2),
        "shoulder": round(measurements["shoulder_cm"], 2),
        "torso": round(measurements["torso_height"], 2),
        "side_depth": round(measurements["side_depth"], 2),
        "status": "modeling",
    }

    files = {
        "front_view": ("front.jpg", front, "image/jpeg"),
        "side_view": ("side.jpg", side, "image/jpeg"),
    }
    
    

    async with httpx.AsyncClient() as client:
        response = await client.post(
            avatar_endpoint,
            data=data,
            files=files,
        )

    response.raise_for_status()
    return response.json()

async def upload_session_details(avatar_id: str, session_id: str) -> dict:
    data = {
        "avatar": avatar_id,
        "status": "pending",
        "session_id": session_id,
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            session_endpoint,
            data=data
        )

    response.raise_for_status()
    return response.json()

async def update_avatar_with_model(avatar_id: str, glb_url: str):
    try:
        # Step 1: Download the GLB file
        async with httpx.AsyncClient() as client:
            glb_response = await client.get(glb_url)
            glb_response.raise_for_status()
            glb_bytes = glb_response.content

        # Step 2: Prepare multipart form-data for PocketBase upload
        files = {
            "unrigged_glb": ("model.glb", glb_bytes, "model/gltf-binary"),
        }
        data = {
            "status": "rigging"
        }

        # Step 3: Send PATCH request to update the avatar record
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{avatar_endpoint}/{avatar_id}",
                data=data,
                files=files
            )
            response.raise_for_status()
            print(f"Avatar {avatar_id} updated with GLB and status set to 'rigging'")

    except Exception as e:
        print(f"Failed to update avatar {avatar_id} with model: {e}")
        
async def update_session_complete(session_id: str, glb_url: str):
    try:
        async with httpx.AsyncClient() as client:
            # Update session where session_id field matches the given session_id
            # First, get the record ID from the session_id
            list_resp = await client.get(session_endpoint, params={
                "filter": f"session_id='{session_id}'"
            })
            list_resp.raise_for_status()
            items = list_resp.json().get("items", [])

            if not items:
                print(f"No session found with session_id: {session_id}")
                return

            record_id = items[0]["id"]

            update_data = {
                "status": "complete",
                "mesh_download_url": glb_url
            }

            # Update the session record
            patch_resp = await client.patch(f"{session_endpoint}/{record_id}", json=update_data)
            patch_resp.raise_for_status()
            print(f"Session {session_id} marked as complete with mesh URL.")

    except Exception as e:
        print(f"Failed to update session {session_id}: {e}")

def get_image_url_of_avatar_source(avatar_id: str, front_filename: str, side_filename: str):    
    return [
        f"{POCKETBASE_URL}/api/files/Avatars/{avatar_id}/{front_filename}",
        f"{POCKETBASE_URL}/api/files/Avatars/{avatar_id}/{side_filename}"
    ]