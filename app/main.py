from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, APIRouter
from loguru import logger

from app.endpoints.router import router
from .config import config
from .database.connector import sessionmanager, create_tables

root_router = APIRouter()

root_router.include_router(router)


async def on_startup():
    logger.info("Starting..")
    await create_tables()


async def on_shutdown():
    logger.info("Stopping..")
    if sessionmanager._engine is not None:
        await sessionmanager.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await on_startup()
    yield
    await on_shutdown()


app = FastAPI(lifespan=lifespan)
app.include_router(root_router)

if __name__ == "__main__":
    uvicorn.run(app, host=config.system.host, port=config.system.port)
