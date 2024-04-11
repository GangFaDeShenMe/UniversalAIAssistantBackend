import random
import string
from typing import Union

from sqlalchemy import Column, Integer, String, ForeignKey, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.config import config


class InviteCode(Base):
    __tablename__ = 'invite_codes'

    code = Column(String(10), nullable=False, unique=True, index=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    owner = relationship("User", back_populates="invite_code", foreign_keys='InviteCode.owner_id')
    use_count = Column(Integer, default=0, nullable=False)

    def __init__(self, user, **kwargs):
        super().__init__(**kwargs)
        self.owner_id = user.id

    def __str__(self):
        return self.code

    class InviteCodeError(Exception):
        def __init__(self, msg):
            super().__init__("Internal Invite Code Error" if not msg else msg)

    class NoSuchCodeError(InviteCodeError):
        def __init__(self, code: str):
            super().__init__(f"Code {code} is invalid")

    class MaxAllowedBindingCountExceededError(InviteCodeError):
        def __init__(self):
            super().__init__(f"Max allowed code binding count exceeded")

    class BindCodeOwnerConflictError(InviteCodeError):
        def __init__(self):
            super().__init__("Cannot bind code owner")

    class CircularBindingError(InviteCodeError):
        def __init__(self):
            super().__init__("Cannot bind own invitees")

    @classmethod
    async def create(cls, session: AsyncSession, user) -> "InviteCode":
        invite_code = cls(user=user)
        invite_code.code = await cls.generate_code(session=session)
        session.add(invite_code)
        return invite_code

    @classmethod
    async def get(
            cls,
            session: AsyncSession,
            id: int = None,
            code: str = None,
            owner=None
    ) -> Union["InviteCode", None]:
        """

        :param session:
        :param id:
        :param code:
        :param owner:
        :return:
        """
        stmt = select(cls)
        if id is not None:
            stmt = stmt.filter_by(id=id)
        if code is not None:
            stmt = stmt.filter_by(code=code)
        if owner is not None:
            stmt = stmt.filter_by(owner_id=owner.id)

        result = await session.execute(stmt)
        return result.scalars().first()

    @classmethod
    async def generate_code(cls, session: AsyncSession) -> str:
        while True:
            code = ''.join(random.choices(string.ascii_letters + string.digits, k=config.referral.invite_code_length))
            if not await cls.get(session, code=code):
                return code
