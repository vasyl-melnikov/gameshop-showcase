from typing import List

from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from starlette import status

from app.api.common import (TEMP_USER_CODE_REQUEST_PREFIX, AuthorizedRequest,
                            generate_common_redis_key, get_token_data)
from app.business_logic.auth import hash_password, verify_password
from app.db import AsyncSession, get_session
from app.db.managers.orders import get_orders_by_user_id
from app.db.managers.user_manager import (get_user_by_email, get_user_by_ukey,
                                          update_user)
from app.dto_schemas.auth import MFACode, Roles, TokenData
from app.dto_schemas.order import OrderResponseModel
from app.dto_schemas.user import (EmailOnlyUser, PasswordOnlyUser,
                                  UserChangeEmail, UserChangePassword,
                                  UserResetPassword, UserResponseModel,
                                  UserRoleResponseModel,
                                  UserUpdatePersonalInfo)
from app.email_sender import EmailSender, get_email_sender
from app.redis_cache import get_redis_client
from app.utils import generate_random_mfa_code, generate_string

DEFAULT_CHANGE_PASSWORD_LINK_EXPIRE = 300  # in seconds
TEMPORARY_PASSWORD_RESET_TOKEN_LENGTH = 256
PASSWORD_REQUEST_PREFIX = "password_change_request"
EMAIL_REQUEST_PREFIX = "email_change_request"
PASSWORD_RESET_REQUEST_PREFIX = "password_reset_request"
SETUP_2FA_REQUEST_PREFIX = "2fa_setup_request"

users_router = APIRouter(prefix="/users")

__all__ = ["users_router"]


def generate_redis_key(prefix: str, ukey: str | None, mfa_code: str) -> str:
    return f"{prefix}:{ukey}:{mfa_code}"


@users_router.get("/me", dependencies=[Depends(AuthorizedRequest(role=Roles.USER))])
async def get_user(
    token_data: TokenData = Depends(get_token_data),
    session: AsyncSession = Depends(get_session),
):
    user = await get_user_by_ukey(session, token_data.ukey)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is not found"
        )
    return UserRoleResponseModel.from_orm(user)


@users_router.patch("/me", dependencies=[Depends(AuthorizedRequest(role=Roles.USER))])
async def update_user_personal_info(
    personal_info: UserUpdatePersonalInfo,
    token_data: TokenData = Depends(get_token_data),
    session: AsyncSession = Depends(get_session),
):
    user = await get_user_by_ukey(session, token_data.ukey)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is not found"
        )
    user.first_name = personal_info.first_name
    user.last_name = personal_info.last_name
    await update_user(session, user)
    return UserResponseModel.from_orm(user)


@users_router.post(
    "/me/request_change_password",
    dependencies=[Depends(AuthorizedRequest(role=Roles.USER))],
)
async def change_user_password_request(
    change_pass_request: UserChangePassword,
    session: AsyncSession = Depends(get_session),
    token_data: TokenData = Depends(get_token_data),
    redis_client: Redis = Depends(get_redis_client),
):
    if token_data.ukey is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bad request"
        )

    user = await get_user_by_ukey(session, token_data.ukey)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is not found"
        )

    if not verify_password(change_pass_request.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is wrong"
        )

    new_hashed_password = hash_password(change_pass_request.new_password)

    mfa_code = generate_random_mfa_code()
    key = generate_redis_key(PASSWORD_REQUEST_PREFIX, token_data.ukey, mfa_code)
    await redis_client.setex(
        key, DEFAULT_CHANGE_PASSWORD_LINK_EXPIRE, new_hashed_password
    )
    print(mfa_code)  # print it here for temp debug purposes
    # send email with link


@users_router.patch(
    "/me/change_password",
    dependencies=[Depends(AuthorizedRequest(role=Roles.USER))],
)
async def change_user_password(
    mfa_code: MFACode,
    session: AsyncSession = Depends(get_session),
    token_data: TokenData = Depends(get_token_data),
    redis_client: Redis = Depends(get_redis_client),
):
    key = generate_redis_key(PASSWORD_REQUEST_PREFIX, token_data.ukey, mfa_code.code)
    new_hashed_pass_bytes: bytes | None = await redis_client.get(key)
    if new_hashed_pass_bytes is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bad request"
        )

    new_hashed_pass = new_hashed_pass_bytes.decode("utf-8")

    if token_data.ukey is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bad request"
        )

    user = await get_user_by_ukey(session, token_data.ukey)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is not found"
        )

    user.hashed_password = new_hashed_pass
    await update_user(session, user)

    return UserResponseModel.from_orm(user)


@users_router.post(
    "/me/request_change_email",
    dependencies=[Depends(AuthorizedRequest(role=Roles.USER))],
)
async def change_user_email_request(
    change_email_request: UserChangeEmail,
    token_data: TokenData = Depends(get_token_data),
    redis_client: Redis = Depends(get_redis_client),
):
    mfa_code = generate_random_mfa_code()
    key = generate_redis_key(EMAIL_REQUEST_PREFIX, token_data.ukey, mfa_code)
    await redis_client.setex(
        key, DEFAULT_CHANGE_PASSWORD_LINK_EXPIRE, change_email_request.email
    )
    print(mfa_code)  # print it here for temp debug purposes
    # send email with link


@users_router.patch(
    "/me/change_email",
    dependencies=[Depends(AuthorizedRequest(role=Roles.USER))],
)
async def change_user_email(
    mfa_code: MFACode,
    session: AsyncSession = Depends(get_session),
    token_data: TokenData = Depends(get_token_data),
    redis_client: Redis = Depends(get_redis_client),
):
    if token_data.ukey is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bad request"
        )

    key = generate_redis_key(EMAIL_REQUEST_PREFIX, token_data.ukey, mfa_code.code)
    new_email_bytes: bytes | None = await redis_client.get(key)
    if new_email_bytes is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bad request"
        )

    new_email = new_email_bytes.decode("utf-8")

    user = await get_user_by_ukey(session, token_data.ukey)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is not found"
        )

    user.email = new_email

    await update_user(session, user)

    return UserResponseModel.from_orm(user)


@users_router.post("/request_password_reset")
async def reset_user_password_request(
    reset_pass_request: UserResetPassword,
    redis_client: Redis = Depends(get_redis_client),
    session: AsyncSession = Depends(get_session),
):
    user = await get_user_by_email(session, reset_pass_request.email)
    if not user:
        return {}
    password_reset_token = generate_string(TEMPORARY_PASSWORD_RESET_TOKEN_LENGTH)
    key = generate_redis_key(PASSWORD_RESET_REQUEST_PREFIX, None, password_reset_token)
    await redis_client.setex(
        key, DEFAULT_CHANGE_PASSWORD_LINK_EXPIRE, reset_pass_request.email
    )
    print(password_reset_token)  # print it here for temp debug purposes
    # send email with link


@users_router.patch("/reset_password/{reset_pass_token}")
async def reset_user_pass(
    reset_pass_token: str,
    new_password_request: PasswordOnlyUser,
    session: AsyncSession = Depends(get_session),
    redis_client: Redis = Depends(get_redis_client),
):
    key = generate_redis_key(PASSWORD_RESET_REQUEST_PREFIX, None, reset_pass_token)
    email_bytes: bytes | None = await redis_client.get(key)
    if email_bytes is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bad request"
        )

    email = email_bytes.decode("utf-8")

    user = await get_user_by_email(session, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is not found"
        )

    user.hashed_password = hash_password(new_password_request.password)

    await update_user(session, user)

    return UserResponseModel.from_orm(user)


@users_router.post(
    "/me/request_enable_2fa",
    dependencies=[Depends(AuthorizedRequest(role=Roles.USER))],
)
async def request_enable_2fa(
    token_data: TokenData = Depends(get_token_data),
    redis_client: Redis = Depends(get_redis_client),
    session: AsyncSession = Depends(get_session),
):
    user = await get_user_by_ukey(session, token_data.ukey)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is not found"
        )

    if user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is already enabled"
        )

    mfa_code = generate_random_mfa_code()
    key = generate_redis_key(SETUP_2FA_REQUEST_PREFIX, token_data.ukey, mfa_code)
    await redis_client.setex(key, DEFAULT_CHANGE_PASSWORD_LINK_EXPIRE, token_data.email)
    print(mfa_code)  # print it here for temp debug purposes
    # send email with link


@users_router.patch(
    "/me/enable_2fa",
    dependencies=[Depends(AuthorizedRequest(role=Roles.USER))],
)
async def enable_2fa(
    mfa_code: MFACode,
    session: AsyncSession = Depends(get_session),
    token_data: TokenData = Depends(get_token_data),
    redis_client: Redis = Depends(get_redis_client),
):
    key = generate_redis_key(SETUP_2FA_REQUEST_PREFIX, token_data.ukey, mfa_code.code)
    email_bytes: bytes | None = await redis_client.get(key)
    if email_bytes is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bad request"
        )

    if token_data.ukey is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bad request"
        )

    user = await get_user_by_ukey(session, token_data.ukey)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is not found"
        )

    user.mfa_enabled = True

    await update_user(session, user)

    return UserResponseModel.from_orm(user)


@users_router.post(
    "/me/request_disable_2fa",
    dependencies=[Depends(AuthorizedRequest(role=Roles.USER))],
)
async def request_disable_2fa(
    token_data: TokenData = Depends(get_token_data),
    redis_client: Redis = Depends(get_redis_client),
    session: AsyncSession = Depends(get_session),
):
    user = await get_user_by_ukey(session, token_data.ukey)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is not found"
        )

    if not user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is already disabled"
        )

    mfa_code = generate_random_mfa_code()
    key = generate_redis_key(SETUP_2FA_REQUEST_PREFIX, token_data.ukey, mfa_code)
    await redis_client.setex(key, DEFAULT_CHANGE_PASSWORD_LINK_EXPIRE, token_data.email)
    print(mfa_code)  # print it here for temp debug purposes
    # send email with link


@users_router.patch(
    "/me/disable_2fa",
    dependencies=[Depends(AuthorizedRequest(role=Roles.USER))],
)
async def disable_2fa(
    mfa_code: MFACode,
    session: AsyncSession = Depends(get_session),
    token_data: TokenData = Depends(get_token_data),
    redis_client: Redis = Depends(get_redis_client),
):
    key = generate_redis_key(SETUP_2FA_REQUEST_PREFIX, token_data.ukey, mfa_code.code)
    email_bytes: bytes | None = await redis_client.get(key)
    if email_bytes is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bad request"
        )

    if token_data.ukey is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bad request"
        )

    user = await get_user_by_ukey(session, token_data.ukey)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is not found"
        )

    user.mfa_enabled = False

    await update_user(session, user)

    return UserResponseModel.from_orm(user)


@users_router.post(
    "/temp/send-verification",
)
async def send_code_for_temp_conversion(
    user_model: EmailOnlyUser,
    email_sender: EmailSender = Depends(get_email_sender),
    session: AsyncSession = Depends(get_session),
    redis_client: Redis = Depends(get_redis_client),
):
    user = await get_user_by_email(session, user_model.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is not found"
        )
    if not user.temporary:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is not temporary"
        )

    key = generate_common_redis_key(
        TEMP_USER_CODE_REQUEST_PREFIX, user.ukey
    )  # using ukey only conveniently overwrites previous code
    code = generate_random_mfa_code()
    await redis_client.set(key, code, ex=180)

    await email_sender.send_message(
        subject="Your registration verification code",
        text=f"Your code is:\n\n" f"{code}" f"\n\nDo not share.",
        to=[user.email],
    )


@users_router.get(
    "/me/orders",
    dependencies=[Depends(AuthorizedRequest(role=Roles.USER))],
    response_model=List[OrderResponseModel],
)
async def get_user_orders(
    token_data: TokenData = Depends(get_token_data),
    session: AsyncSession = Depends(get_session),
):
    user = await get_user_by_ukey(session, token_data.ukey)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is not found"
        )
    orders = await get_orders_by_user_id(session, user.id)
    return orders
