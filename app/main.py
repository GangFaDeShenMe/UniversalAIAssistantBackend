import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, APIRouter
from loguru import logger

from app.endpoints.router import router
from app.config import config
from app.database.connector import (sessionmanager, create_tables)

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
    try:
        uvicorn.run(app, host=config.system.host, port=config.system.port)
    except KeyboardInterrupt:
        exit(0)
