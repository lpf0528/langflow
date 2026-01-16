from fastapi import APIRouter
from .system.api.user import router as user_router
from .mcp_server.api import router as mcp_router

api_router = APIRouter()
# api_router.include_router(login.router)
api_router.include_router(user_router)
api_router.include_router(mcp_router)
