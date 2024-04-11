import pytest
from datetime import date

from tests.clean_db import clean_db
from app.database.models.daily_stats import DailyStats
from app.database.connector import sessionmanager

# todo format and add more tests
async def test_get_existing(clean_db):
    async with sessionmanager.session() as session:
        # Setup: create a DailyStats instance for today
        new_stats = DailyStats(date_interval=date.today(), api_calls=10)
        session.add(new_stats)
        await session.commit()

        # Exercise: Retrieve the created DailyStats instance
        retrieved_stats = await DailyStats.get(session, date.today())

        # Verify: Check if the retrieved instance matches the created one
        assert retrieved_stats is not None
        assert retrieved_stats.api_calls == 10
        assert retrieved_stats.date_interval == date.today()


async def test_get_non_existing(clean_db):
    async with sessionmanager.session() as session:
        # Exercise: Try to retrieve a DailyStats instance for today when none exists
        retrieved_stats = await DailyStats.get(session, date.today())

        # Verify: Check if no instance is returned
        assert retrieved_stats is None


async def test_get_or_create_existing(clean_db):
    async with sessionmanager.session() as session:
        # Setup: create a DailyStats instance for today
        new_stats = DailyStats(date_interval=date.today(), api_calls=20)
        session.add(new_stats)
        await session.commit()

        # Exercise: Use get_or_create, which should retrieve the existing instance
        retrieved_stats = await DailyStats.get_or_create(session)

        # Verify: Check if the retrieved instance matches the created one
        assert retrieved_stats is not None
        assert retrieved_stats.api_calls == 20
        assert retrieved_stats.date_interval == date.today()


async def test_get_or_create_non_existing(clean_db):
    async with sessionmanager.session() as session:
        # Exercise: Use get_or_create when no instance exists for today
        created_stats = await DailyStats.get_or_create(session)

        # Verify: Check if a new instance was created and returned
        assert created_stats is not None
        assert created_stats.date_interval == date.today()
        # Optionally, verify default values
        assert created_stats.api_calls == 0
