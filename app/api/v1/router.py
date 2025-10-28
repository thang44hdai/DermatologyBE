from fastapi import APIRouter
from app.api.v1.endpoints import health, prediction, users, auth, pharmacy

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth")  # Tags defined in endpoints
api_router.include_router(prediction.router, prefix="/prediction", tags=["Prediction"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(pharmacy.router, prefix="/pharmacies", tags=["Pharmacy Management (Admin)"])
