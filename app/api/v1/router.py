from fastapi import APIRouter
from app.api.v1.endpoints import health, prediction, users

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(prediction.router, prefix="/prediction", tags=["Prediction"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
