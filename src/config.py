from decouple import config
from pathlib import Path


PROJ_ROOT = Path(__file__).resolve().parents[1]

CUBE_URL = config('CUBE_URL', default='https://api.csm.ai/v3/sessions')
CUBE_API_KEY = config('CUBE_API_KEY', default='')
POCKETBASE_URL = config('POCKETBASE_URL', default='https://fittingroom.hatchwise.me')