from app.database.models.invite_code import InviteCode
from app.database.models.user import User
from app.config import config
from app.database.connector import sessionmanager
import pytest
from tests.clean_db import clean_db


async def test_create_with_invite_code(clean_db):
    async with sessionmanager.session() as session:
        qq_user = await User.create_with_invite_code(qq_number="1234056789", session=session)
        email_user = await User.create_with_invite_code(email="1@1.com", session=session)
        wechat_user = await User.create_with_invite_code(wechat_id="123456", session=session)

        assert qq_user.id == 1
        assert qq_user.qq_number == "1234056789"
        assert qq_user.email is None

        with pytest.raises(ValueError):
            bare_user = await User.create_with_invite_code(session=session)

        with pytest.raises(User.UserAlreadyExistsError):
            duplicated_user = await User.create_with_invite_code(qq_number="1234056789", session=session)

        assert await qq_user.awaitable_attrs.invite_code != await email_user.awaitable_attrs.invite_code
        assert (await qq_user.awaitable_attrs.invite_code).code != (await email_user.awaitable_attrs.invite_code).code


async def test_get(clean_db):
    async with sessionmanager.session() as session:
        # 创建多个用户以测试不同的查询条件
        qq_user = await User.create_with_invite_code(qq_number="1234056789", session=session)
        email_user = await User.create_with_invite_code(email="1@1.com", session=session)
        wechat_user = await User.create_with_invite_code(wechat_id="123456", session=session)
        phone_user = await User.create_with_invite_code(phone_number="12345678901", session=session)

        # 通过uuid查询
        uuid_user = await User.create_with_invite_code(email="uuid@user.com", session=session)
        uuid_str = str(uuid_user.uuid)

        # 测试通过不同的标识符查询用户
        assert await User.get(qq_number="1234056789", session=session) == qq_user
        assert await User.get(id=email_user.id, session=session) == email_user
        assert await User.get(wechat_id="123456", session=session) == wechat_user
        assert await User.get(phone_number="12345678901", session=session) == phone_user
        assert await User.get(email="1@1.com", session=session) == email_user
        assert await User.get(uuid=uuid_str, session=session) == uuid_user

        # 测试在没有提供任何条件时，查询返回None的情况
        assert await User.get(session=session) is None

        # 测试查询不存在的用户
        assert await User.get(qq_number="nonexistent", session=session) is None
        assert await User.get(id=99999, session=session) is None
        assert await User.get(wechat_id="nonexistent", session=session) is None
        assert await User.get(phone_number="nonexistent", session=session) is None
        assert await User.get(email="nonexistent@user.com", session=session) is None
        assert await User.get(uuid="nonexistent-uuid", session=session) is None


async def test_charge(clean_db):
    async with sessionmanager.session() as session:
        # 创建用户和邀请人
        user = await User.create_with_invite_code(email="user@example.com", session=session)

        # 正常充值操作
        charge_amount = 1000  # 1000 cents
        assert await user.charge(session, charge_amount, type="charge")
        assert user.balance_in_cents == charge_amount + config.billing.balance_in_cents
        assert user.total_recharged_amount_in_cents == charge_amount

        # 充值类型为"bonus"
        bonus_amount = 500
        assert await user.charge(session, bonus_amount, type="bonus")
        assert user.balance_in_cents == charge_amount + bonus_amount + config.billing.balance_in_cents
        assert user.total_bonus_amount_in_cents == bonus_amount

        # 传入负数金额
        with pytest.raises(ValueError):
            await user.charge(session, -100)

        # 传入0作为金额
        assert await user.charge(session, 0)
        # 确保余额未改变
        assert user.balance_in_cents == charge_amount + bonus_amount + config.billing.balance_in_cents

        with pytest.raises(TypeError):
            await user.charge(session, "not_an_integer", type="charge")
        # 确保余额未因异常而改变
        assert user.balance_in_cents == charge_amount + bonus_amount + config.billing.balance_in_cents


async def test_ban(clean_db):
    async with sessionmanager.session() as session:
        # 创建一个用户用于测试
        user = await User.create_with_invite_code(email="test@user.com", session=session)

        # 测试封禁用户
        ban_result = await user.ban(session=session, scheme="ban")
        assert ban_result is True
        assert user.is_banned is True
        # 此处可以添加更多的断言来检查封禁的具体效果，例如封禁时间等

        # 重新从数据库中获取用户信息，以验证更改是否已持久化
        reloaded_user = await User.get(email="test@user.com", session=session)
        assert reloaded_user.is_banned is True

        # 测试解封用户
        unban_result = await user.ban(session=session, scheme="unban")
        assert unban_result is True
        assert user.is_banned is False

        # 再次从数据库中获取用户信息，以验证更改是否已持久化
        reloaded_user = await User.get(email="test@user.com", session=session)
        assert reloaded_user.is_banned is False

        # 测试无效方案
        with pytest.raises(ValueError) as exc_info:
            await user.ban(session=session, scheme="invalid_scheme")
        assert "Invalid scheme provided" in str(exc_info.value)

        # 验证数据库操作是否已回滚（即用户的封禁状态未发生变化）
        reloaded_user = await User.get(email="test@user.com", session=session)
        assert reloaded_user.is_banned is False


async def test_pay(clean_db):
    async with sessionmanager.session() as session:
        # Setup: Create a user with a specific balance
        user = await User.create_with_invite_code(email="paytest@user.com", session=session)
        user.balance_in_cents = 1000  # \$10
        user.gifted_balance_in_cents = 500  # \$5 of the balance is gifted
        await session.commit()

        # Case 1: Pay with a negative amount (should raise ValueError)
        with pytest.raises(ValueError):
            await user.pay(session=session, amount=-100)

        # Case 2: Pay with zero amount (should succeed and not change balances)
        assert await user.pay(session=session, amount=0)
        assert user.balance_in_cents == 1000
        assert user.gifted_balance_in_cents == 500

        # Case 3: Pay an amount less than the gifted balance
        assert await user.pay(session=session, amount=300)  # Pay \$3
        assert user.balance_in_cents == 700  # Total balance should now be \$7
        assert user.gifted_balance_in_cents == 200  # Gifted balance should now be \$2

        # Case 4: Pay an amount that exceeds the gifted balance but not the total balance
        assert await user.pay(session=session, amount=600)  # Pay \$6
        assert user.balance_in_cents == 100  # Total balance should now be \$1
        assert user.gifted_balance_in_cents == 0  # Gifted balance should now be \$0

        # Case 5: Attempt to pay more than the total balance (should log a warning and proceed)
        await user.pay(session=session, amount=200)  # Attempt to pay \$2 when balance is \$1

        # Reload user from DB to confirm balance changes were persisted
        reloaded_user = await User.get(id=user.id, session=session)
        assert reloaded_user.balance_in_cents == -100
        assert reloaded_user.gifted_balance_in_cents == 0


async def test_bind_invite_code(clean_db):
    async with sessionmanager.session() as session:
        # 创建用户和邀请码
        user = await User.create_with_invite_code(email="user@test.com", session=session)
        inviter = await User.create_with_invite_code(email="inviter@test.com", session=session)
        reloaded_inviter = await User.get(id=inviter.id, session=session)
        invite_code = inviter.invite_code
        assert reloaded_inviter.invite_code == invite_code

        # 成功绑定邀请码
        assert await user.bind_invite_code(session=session, code=invite_code.code) is True
        assert user in await inviter.awaitable_attrs.invitees

        # 尝试重复绑定邀请码
        with pytest.raises(User.RepeatedlyBindInviteCodeError):
            await user.bind_invite_code(session=session, code=invite_code.code)

        # 使用不存在的邀请码
        with pytest.raises(InviteCode.NoSuchCodeError):
            await inviter.bind_invite_code(session=session, code="nonexistentcode")

        # 超过邀请码的最大使用次数
        invite_code.use_count = config.referral.invite_code_max_usage
        await session.commit()
        with pytest.raises(InviteCode.MaxAllowedBindingCountExceededError):
            another_user = await User.create_with_invite_code(email="another@test.com", session=session)
            await another_user.bind_invite_code(session=session, code=invite_code.code)
        invite_code.use_count = len(await inviter.awaitable_attrs.invitees)

        # 尝试绑定自己的邀请码
        await session.commit()
        with pytest.raises(InviteCode.BindCodeOwnerConflictError):
            await inviter.bind_invite_code(session=session, code=invite_code.code)

        # 尝试形成循环邀请链
        invitee = await User.create_with_invite_code(email="invitee@test.com", session=session)
        await invitee.bind_invite_code(session=session, code=invite_code.code)
        with pytest.raises(InviteCode.CircularBindingError):
            await inviter.bind_invite_code(session=session, code=invitee.invite_code.code)

        # 验证数据库操作是否成功
        reloaded_inviter = await User.get(email="inviter@test.com", session=session)
        reloaded_user = await User.get(email="user@test.com", session=session)
        assert reloaded_user.inviter_id == inviter.id

        # 验证邀请码使用次数增加
        reloaded_invite_code = await InviteCode.get(session=session, code=invite_code.code)
        assert reloaded_invite_code.use_count == 2  # user, invitee
