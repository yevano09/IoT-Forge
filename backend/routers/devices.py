from fastapi import APIRouter
from backend.database import db

router = APIRouter()


@router.get("/devices")
async def list_devices():
    return await db.get_devices()