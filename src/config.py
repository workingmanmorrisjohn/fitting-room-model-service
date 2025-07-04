from decouple import config
from pathlib import Path


PROJ_ROOT = Path(__file__).resolve().parents[1]

CUBE_URL = config('CUBE_URL', default='https://api.csm.ai')
CUBE_API_KEY = config('CUBE_API_KEY', default='')
POCKETBASE_URL = config('POCKETBASE_URL', default='https://fittingroom.hatchwise.me')
REGISTER_URL = config('POCKETBASE_URL', default='https://register.hatchwise.me')
SIZE_URL = config('SIZE_URL', default='https://size.hatchwise.me')