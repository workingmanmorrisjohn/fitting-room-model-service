from rembg import remove
from PIL import Image
from io import BytesIO

from .pose_estimate_module import extract_measurements_from_images_with_bytes

async def remove_background(image_bytes: bytes) -> bytes:
    # Use rembg to remove background
    output = remove(image_bytes)

    # Optionally convert to PNG to preserve transparency
    img = Image.open(BytesIO(output)).convert("RGBA")
    byte_io = BytesIO()
    img.save(byte_io, format="PNG")
    return byte_io.getvalue()

async def get_measurements(front: bytes, side: bytes, height: int) -> dict:
    measurements = extract_measurements_from_images_with_bytes(front, side, height)
    
    return measurements 