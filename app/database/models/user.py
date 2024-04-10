from datetime import datetime, timedelta

import uuid
from typing import Optional, Union, List

from loguru import logger
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Interval, ForeignKey, UUID, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, selectinload, Mapped

from app.database.base import Base
from app.database.models.daily_stats import DailyStats
from app.database.models.invite_code import InviteCode
from app.config import config


class User(Base):
    __tablename__ = 'users'

    # --- Identifying ---
    # -- Internal --
    id = Column(Integer, primary_key=True)
    uuid = Column(UUID, index=True, unique=True, nullable=False)
    # -- External --
    qq_number = Column(String(15), nullable=True, index=True)
    wechat_id = Column(String(15), nullable=True, index=True)
    phone_number = Column(String(20), nullable=True, index=True)
    email = Column(String(30), nullable=True, index=True)

    # --- Safety ---
    is_banned = Column(Boolean, default=False, nullable=False)
    current_banned_since = Column(DateTime)
    current_banned_period = Column(Interval)
    banned_count = Column(Integer, default=0, nullable=False)
    violation_count = Column(Integer, default=0, nullable=False)

    # --- Billing ---
    balance_in_cents = Column(Integer, default=config.billing.balance_in_cents, nullable=False)
    gifted_balance_in_cents = Column(Integer, default=config.billing.balance_in_cents, nullable=False)
    billing_rate = Column(Integer, default=config.billing.billing_rate, nullable=False)

    # --- Invitation ---
    invite_code_id = Column(Integer, ForeignKey('invite_codes.id'))
    invite_code = relationship("InviteCode", back_populates="owner", uselist=False,
                               foreign_keys="[InviteCode.owner_id]")
    inviter_id = Column(Integer, ForeignKey('users.id'))
    inviter = relationship("User", remote_side=[id], back_populates="invitees", uselist=False)
    invitees = relationship("User", back_populates="inviter")

    # --- Stats ---
    total_token_usage = Column(Integer, default=0, nullable=False)
    total_recharged_amount_in_cents = Column(Integer, default=0, nullable=False)
    total_bonus_amount_in_cents = Column(Integer, default=0, nullable=False)

    class UserError(Exception):
        pass

    class UserAlreadyExistsError(UserError):
        pass

    @classmethod
    async def create_with_invite_code(
            cls,
            session: AsyncSession,
            **kwargs
    ) -> Union["User", False]:
        """

        :param session:
        :param kwargs: qq_number: str, wechat_id: str, phone_number: str, email: str,
        :return: User object if success else False
        """
        if not any(kwargs.values()):
            raise ValueError("At least one of required user identifier is required")

        user = await cls.get(session=session, **kwargs)
        if user:
            raise cls.UserAlreadyExistsError(f"Attempted to create duplicated user with {kwargs}")
        try:
            user = cls(**kwargs, uuid=uuid.uuid4())
            session.add(user)
            invite_code = await InviteCode.create(session=session, user=user)
            user.invite_code = invite_code
            user.invite_code_id = invite_code.id
            await session.commit()
            return user
        except Exception as e:
            logger.exception(e)
            await session.rollback()
            return False

    @classmethod
    async def get(
            cls,
            session: AsyncSession,
            id: Optional[int] = None,
            uuid: Optional[str] = None,
            qq_number: Optional[str] = None,
            wechat_id: Optional[str] = None,
            phone_number: Optional[str] = None,
            email: Optional[str] = None,
    ) -> Optional["User"]:
        """
        Get a User object from database

        :return: User object if found else None
        """
        conditions = []
        if id is not None:
            conditions.append(cls.id == id)
        if uuid is not None:
            conditions.append(cls.uuid == uuid)
        if qq_number is not None:
            conditions.append(cls.qq_number == qq_number)
        if wechat_id is not None:
            conditions.append(cls.wechat_id == wechat_id)
        if phone_number is not None:
            conditions.append(cls.phone_number == phone_number)
        if email is not None:
            conditions.append(cls.email == email)

        if not conditions:
            return None

        query = select(cls).where(*conditions)

        result = await session.execute(query)
        return result.scalars().first()

    async def charge(self, session: AsyncSession, amount: int, type: str = "charge", ) -> bool:
        """
        Add some balance to user

        :param session:
        :param amount: in cents
        :param type: 'charge' | 'bonus'
        :return: False if internal error
        """
        if amount < 0:
            raise ValueError("Negative amount not allowed, use User.pay() instead")
        if amount == 0:
            return True

        try:
            stats = await DailyStats.get_or_create(session=session)
            self.balance_in_cents += amount

            if type == "charge":
                self.total_recharged_amount_in_cents += amount
                stats.recharged_amount_in_cents += amount

                if config.referral.cash_back_when_invitee_charges and self.inviter_id:
                    inviter = await User.get(id=self.inviter_id, session=session)
                    await inviter.charge(
                        session=session,
                        amount=config.referral.inviter_cash_back_amount_when_invitee_charges_percent * amount,
                        type="bonus"
                    )

            elif type == "bonus":
                self.total_bonus_amount_in_cents += amount
                stats.bonus_amount_in_cents += amount

            await session.commit()

            return True
        except Exception as e:
            logger.exception(e)
            await session.rollback()
            return False

    async def ban(self, session: AsyncSession, duration: timedelta, scheme: str = "ban") -> bool:
        """

        :param session:
        :param duration:
        :param scheme: "ban" | "unban", etc...
        :return:
        """
        do_ban = True if scheme == "ban" else False
        self.is_banned = do_ban
        if do_ban:
            pass
            # todo: interval and stuff
        try:
            await session.commit()
            return True
        except Exception as e:
            logger.exception(e)
            await session.rollback()
            return False

    async def pay(self, session: AsyncSession, amount: int, ) -> bool:
        """
        :param session:
        :param amount: in cents
        :return True if success else False
        """
        if amount < 0:
            raise ValueError("Negative amount not allowed, use User.charge() instead")

        if amount == 0:
            return True

        if amount > self.balance_in_cents:
            logger.warning(
                f"User ID {self.id} attempted to pay {amount} which is more than the balance {self.balance_in_cents}. "
            )

        if self.gifted_balance_in_cents >= amount:
            self.gifted_balance_in_cents -= amount
            self.balance_in_cents -= amount
        else:
            amount_to_pay_from_balance = amount - self.gifted_balance_in_cents
            self.balance_in_cents -= self.gifted_balance_in_cents
            self.gifted_balance_in_cents = 0

            self.balance_in_cents -= amount_to_pay_from_balance
        try:
            stats = await DailyStats.get_or_create(session=session)
            stats.total_user_usage_amount_in_cents += amount

            await session.commit()

            return True
        except Exception as e:
            logger.exception(e)
            await session.rollback()
            return False

    async def bind_invite_code(self, session: AsyncSession, code: str | InviteCode) -> bool:
        """
        :param session:
        :param code:
        :return: True if success else False
        """
        if self.inviter_id:
            raise ValueError("Cannot repeatedly bind")

        if isinstance(code, str):
            invite_code = await InviteCode.get(session=session, code=code)
        else:
            invite_code = code
        if not invite_code:
            raise ValueError("Invalid code")

        if invite_code.use_count >= config.referral.invite_code_max_usage:
            raise ValueError("Max code usage exceeded")

        if invite_code.owner_id == self.id:
            raise ValueError("Cannot bind self")

        inviter = invite_code.owner

        if inviter in await self.awaitable_attrs.invitees:
            raise ValueError("Cannot bind own invitees")

        self.inviter = inviter
        inviter_invitees = await inviter.awaitable_attrs.invitees
        inviter_invitees.append(self)

        inviter.invitees = inviter_invitees

        self.inviter_id = invite_code.owner_id
        invite_code.use_count += 1

        if config.referral.cash_back_when_bind:
            await inviter.charge(
                session=session, type="bonus",
                amount=config.referral.inviter_cash_back_amount_when_bind_in_cents
            )
            await self.charge(
                session=session, type="bonus",
                amount=config.referral.invitee_cash_back_amount_when_bind_in_cents
            )
        stats = await DailyStats.get_or_create(session=session)
        stats.invite_code_binds += 1

        await session.commit()
        return True
