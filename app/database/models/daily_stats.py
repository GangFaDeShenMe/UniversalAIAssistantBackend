from datetime import date

from sqlalchemy import Column, Integer, Date, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..connector import Base


class DailyStats(Base):
    __tablename__ = 'stats'

    id = Column(Integer, primary_key=True)
    date_interval = Column(Date, nullable=False, default=date.today())

    # --- Platform ---
    api_calls = Column(Integer, default=0, nullable=False)
    frontend_types = Column(Integer, default=0, nullable=False)

    # --- AI Usage ---
    # -- OpenAI --

    # Use a specific api key and see platform.openai.com or your api key provider for further stats
    # -- OCR --
    images_ocred = Column(Integer, default=0, nullable=False)
    # -- Stable Diffusion --
    sd_images_generated = Column(Integer, default=0, nullable=False)
    # ...

    # --- Billing ---
    recharged_amount_in_cents = Column(Integer, default=0, nullable=False)
    user_usage_amount_in_cents = Column(Integer, default=0, nullable=False)
    bonus_amount_in_cents = Column(Integer, default=0, nullable=False)

    @classmethod
    async def get(cls, session: AsyncSession, date_interval: date) -> "DailyStats":
        query = select(cls).where(cls.date_interval == date_interval)
        result = await session.execute(query)
        return result.scalars().first()

    @classmethod
    async def get_or_create(cls, session: AsyncSession) -> "DailyStats":
        instance = await cls.get(session, date.today())
        if instance:
            return instance
        else:
            instance = cls(date_interval=date.today())
            session.add(instance)
            await session.commit()
            return instance
