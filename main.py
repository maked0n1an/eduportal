import uvicorn
from fastapi import APIRouter, FastAPI

from src.api.handlers import user_router
from src.api.login_handler import login_router

app = FastAPI(title="eduportal")

main_api_router = APIRouter()
main_api_router.include_router(user_router, prefix="/user", tags=["user"])
main_api_router.include_router(login_router, prefix="/login", tags=["login"])
app.include_router(main_api_router)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
