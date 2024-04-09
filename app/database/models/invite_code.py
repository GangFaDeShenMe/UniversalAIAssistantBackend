import random
import string
from typing import Union

from sqlalchemy import Column, Integer, String, ForeignKey, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..base import Base
from ...config import config


class InviteCode(Base):
    __tablename__ = 'invite_codes'

    id = Column(Integer, primary_key=True)
    code = Column(String(10), nullable=False, unique=True, index=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    use_count = Column(Integer, default=0, nullable=False)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.owner_id = user.id

    @classmethod
    async def create(cls, session: AsyncSession, user) -> "InviteCode":
        invite_code = cls(session=session, user=user)
        invite_code.code = await cls.generate_code(session=session)
        session.add(invite_code)
        return invite_code

    @classmethod
    async def get(cls, session: AsyncSession, id: int = None, code: str = None) -> Union["InviteCode", None]:
        stmt = select(cls)
        if id is not None:
            stmt = stmt.filter_by(id=id)
        if code is not None:
            stmt = stmt.filter_by(code=code)

        result = await session.execute(stmt)
        return result.scalars().first()

    @classmethod
    async def generate_code(cls, session: AsyncSession) -> str:
        while True:
            code = ''.join(random.choices(string.ascii_letters + string.digits, k=config.referral.invite_code_length))
            if not await cls.get(session, code=code):
                return code

    def __str__(self):
        return self.code
