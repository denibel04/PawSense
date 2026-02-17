from fastapi import APIRouter
from app.api.v1.endpoints import upload, predict, chat, report

api_router = APIRouter()

api_router.include_router(upload.router, prefix="/input", tags=["input"])
api_router.include_router(predict.router, prefix="/predict", tags=["predict"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(report.router, prefix="/report", tags=["report"])
