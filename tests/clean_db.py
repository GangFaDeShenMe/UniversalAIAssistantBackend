import pytest
from app.database.connector import drop_tables
from app.main import on_startup


@pytest.fixture()
async def clean_db():
    await drop_tables()
    await on_startup()
    yield
    await drop_tables()
