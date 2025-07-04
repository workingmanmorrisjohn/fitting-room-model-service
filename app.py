from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, status
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from typing import Optional
from contextlib import asynccontextmanager
from src.controller import create_entries, poll_sessions

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic: e.g. start poll_sessions as a background task
    task = asyncio.create_task(poll_sessions())
    yield
    # Shutdown logic: stop the polling task
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.post("/new-avatar", status_code=status.HTTP_201_CREATED)
async def new_avatar(
    background_tasks: BackgroundTasks,
    front_view: UploadFile = File(...),
    side_view: UploadFile = File(...),
    back_view: UploadFile = File(...),
    height: int = Form(...),
    gender: str = Form(...)
):
    front_bytes = await front_view.read()
    side_bytes = await side_view.read()
    back_bytes = await back_view.read()


    background_tasks.add_task(create_entries, front_bytes, side_bytes, back_bytes, height, gender)
    return Response(status_code=status.HTTP_201_CREATED)
