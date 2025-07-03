from ml_service.app import app
from ml_service.api.default import default_router


app.include_router(default_router)
