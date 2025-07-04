from fastapi import APIRouter

from ml_service.api.default import default_router


router = APIRouter()
router.include_router(default_router)
