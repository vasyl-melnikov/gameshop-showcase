from fastapi import APIRouter, Depends, HTTPException, Query
from redis.asyncio import Redis
from starlette import status
from starlette.responses import JSONResponse

from app.api.common import (TEMP_USER_CODE_REQUEST_PREFIX, AuthorizedRequest,
                            generate_common_redis_key, get_logger,
                            get_token_data)
from app.business_logic.auth import (create_access_token,
                                     create_mfa_only_access_token,
                                     hash_password, verify_password)
from app.db import AsyncSession, get_session
from app.db.managers.user_manager import (add_temp_user, add_user,
                                          get_user_by_email, update_user, get_user_by_ukey)
from app.dto_schemas.auth import MFACode, Roles, Token, TokenData, TokenType
from app.dto_schemas.user import (EmailOnlyUser, UserCreate, UserLogin,
                                  UserResponseModel)
from app.redis_cache import get_redis_client
from app.utils import generate_random_mfa_code

login_router = APIRouter(prefix="/login")
register_router = APIRouter(prefix="/register")

__all__ = ["login_router", "register_router"]

AUTH_2FA_REQUEST_PREFIX = "auth-2fa-request-prefix"
DEFAULT_AUTH_2FA_CODE_EXP = 300  # 5 minutes


@login_router.post("")
async def login(
    user_login_model: UserLogin,
    session: AsyncSession = Depends(get_session),
    redis_client: Redis = Depends(get_redis_client),
):
    user = await get_user_by_email(session, user_login_model.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User email or password is invalid",
        )

    if not verify_password(user_login_model.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User email or password is invalid",
        )

    if user.mfa_enabled:
        access_token = create_mfa_only_access_token(user.ukey, user_login_model.email)
        mfa_code = generate_random_mfa_code()
        key = f"{AUTH_2FA_REQUEST_PREFIX}:{user.ukey}"
        await redis_client.setex(key, DEFAULT_AUTH_2FA_CODE_EXP, mfa_code)
        print(mfa_code)  # print it here for temp debug purposes
    else:
        access_token = create_access_token(user.ukey, user_login_model.email, user.role)

    mfa_enabled = str(user.mfa_enabled).lower()
    response = Token(access_token=access_token, token_type=TokenType.BEARER)

    return JSONResponse(
        content=response.model_dump(), headers={"X-MFA-Required": mfa_enabled}
    )


@login_router.post(
    "/auth",
    dependencies=[
        Depends(AuthorizedRequest(role=Roles.PARTIALLY_LOGGED_IN, exact_role=True))
    ],
    response_model=Token,
)
async def authenticate(
    mfa_code: MFACode,
    token_data: TokenData = Depends(get_token_data),
    redis_client: Redis = Depends(get_redis_client),
    session: AsyncSession = Depends(get_session)
):
    user = await get_user_by_ukey(session, token_data.ukey)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    key = f"{AUTH_2FA_REQUEST_PREFIX}:{token_data.ukey}"
    saved_code_bytes: bytes = await redis_client.get(key)
    saved_code = saved_code_bytes.decode("utf-8")

    if mfa_code.code != saved_code:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid authorization code."
        )

    access_token = create_access_token(token_data.ukey, token_data.email, user.role)

    return Token(access_token=access_token, token_type=TokenType.BEARER)


@register_router.post("", response_model=UserResponseModel)
async def register(
    user_creation_model: UserCreate, session: AsyncSession = Depends(get_session)
):
    user = await get_user_by_email(session, user_creation_model.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with such email address already exist",
        )

    user_creation_model.password = hash_password(user_creation_model.password)
    user = await add_user(session, user_create_model=user_creation_model)
    return UserResponseModel.from_orm(user)


@register_router.post("/temporary", response_model=Token)
async def register_temp(
    user_creation_model: EmailOnlyUser, session: AsyncSession = Depends(get_session)
):
    user = await get_user_by_email(session, user_creation_model.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with such email address already exist",
        )

    user = await add_temp_user(session, user_create_model=user_creation_model)
    access_token = create_access_token(user.ukey, user.email, Roles.USER)

    return Token(access_token=access_token, token_type=TokenType.BEARER)


@register_router.post("/convert-temp", response_model=UserResponseModel)
async def convert_temp(
    user_creation_model: UserCreate,
    code: str = Query(...),
    redis_client: Redis = Depends(get_redis_client),
    session: AsyncSession = Depends(get_session),
):
    user = await get_user_by_email(session, user_creation_model.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with such email address already exist",
        )
    if not user.temporary:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is not temporary"
        )

    key = generate_common_redis_key(TEMP_USER_CODE_REQUEST_PREFIX, user.ukey)
    code_bytes: bytes = await redis_client.get(key)
    if not code_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Code not found or expired",
        )

    if code != code_bytes.decode("utf-8"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect code",
        )

    user.first_name = user_creation_model.first_name or None
    user.last_name = user_creation_model.last_name or None
    user.username = user_creation_model.username
    user.hashed_password = hash_password(user_creation_model.password)
    user.temporary = False

    updated_user = await update_user(session, user)
    return UserResponseModel.from_orm(updated_user)
