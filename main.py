import uvicorn
from fastapi import APIRouter, FastAPI

from src.api.handlers import user_router
from src.api.login_handler import login_router
from src.api.service import service_router
from src.config import db_settings

app = FastAPI(title="eduportal")

main_api_router = APIRouter()
main_api_router.include_router(user_router, prefix="/user", tags=["user"])
main_api_router.include_router(login_router, prefix="/login", tags=["login"])
main_api_router.include_router(service_router, tags=["service"])

app.include_router(main_api_router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=db_settings.APP_PORT)
