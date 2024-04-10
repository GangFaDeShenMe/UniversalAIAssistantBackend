from app.database.models.invite_code import InviteCode
from app.database.models.user import User
from app.config import config
from main import on_startup
from database.connector import sessionmanager, create_tables, get_db_session, drop_tables

import asyncio
import pytest


@pytest.mark.asyncio
async def test_main():
    await drop_tables()
    await on_startup()
    async with sessionmanager.session() as session:
        qq_user = await User.create_with_invite_code(qq_number="1234056789", session=session)
        email_user = await User.create_with_invite_code(email="1@1.com", session=session)
        wechat_user = await User.create_with_invite_code(wechat_id="123456", session=session)

        await qq_user.bind_invite_code(session=session, code=await InviteCode.get(owner=wechat_user, session=session))
        try:
            await wechat_user.bind_invite_code(session=session,
                                               code=await InviteCode.get(owner=qq_user, session=session))
        except Exception as e:
            assert str(e) == "Cannot bind own invitees"


asyncio.run(test_main())
