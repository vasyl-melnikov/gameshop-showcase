from typing import List

from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from starlette import status

from app.api.common import (SG_REQUEST_PREFIX, AuthorizedRequest,
                            generate_common_redis_key,
                            get_id_from_common_redis_key, get_token_data)
from app.business_logic.auth import resolve_role_access
from app.db import AsyncSession, get_session
from app.db.managers.exceptions import (ChangeRequestNotFound,
                                        ChangeRequestNotPending, GameNotFound,
                                        UserNotFound)
from app.db.managers.game_manager import (approve_game_change_request,
                                          disapprove_game_change_request,
                                          get_game_change_requests)
from app.db.managers.user_manager import (get_user_by_email,
                                          update_role_by_email)
from app.dto_schemas.auth import Roles, TokenData
from app.dto_schemas.game import GameResponseModel
from app.dto_schemas.game_change_request import GameChangeRequestResponseModel
from app.dto_schemas.steam_guard import (SetSteamGuardCodeRequest,
                                         SteamGuardPendingRequestResponse,
                                         SteamGuardRequestStatus,
                                         SteamGuardSetModel, SteamGuardStatus)
from app.dto_schemas.user import UserRolePatch, UserRoleResponseModel
from app.redis_cache import get_redis_client
from app.s3 import get_s3_client, S3Client
from app.settings import settings
from app.utils import async_islice

admins_router = APIRouter(prefix="/admins")

__all__ = ["admins_router"]


@admins_router.patch(
    "/me/users/role", dependencies=[Depends(AuthorizedRequest(role=Roles.ADMIN))]
)
async def patch_user_role(
    user_role_patch: UserRolePatch,
    session: AsyncSession = Depends(get_session),
    token_data: TokenData = Depends(get_token_data),
):
    try:
        user = await get_user_by_email(session, user_role_patch.email)
    except UserNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    resolve_role_access(
        token_data.role, user.role, strict=True
    )  # your role is not less than user's role you try to change
    resolve_role_access(
        token_data.role, user_role_patch.role, strict=True
    )  # your role is not less than role you try to assign
    user = await update_role_by_email(
        session, user_role_patch.email, user_role_patch.role
    )

    return UserRoleResponseModel.from_orm(user)


@admins_router.post(
    "/me/moderator-requests/{request_id}/approve",
    dependencies=[Depends(AuthorizedRequest(role=Roles.ADMIN))],
)
async def confirm_game_change_request(
    request_id: int,
    session: AsyncSession = Depends(get_session),
    s3_client: S3Client = Depends(get_s3_client)
):
    try:
        game, old_game = await approve_game_change_request(session, request_id)
        blob_s3_key = old_game.game_img_url.split('/')[2]
        await s3_client.delete_object(Bucket=settings.aws.bucket_name, Key=blob_s3_key)
    except ChangeRequestNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game change request not found",
        )
    except ChangeRequestNotPending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Game change request is not pending",
        )
    except GameNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Game not found"
        )

    return GameResponseModel.from_orm(game)


@admins_router.post(
    "/me/moderator-requests/{request_id}/disapprove",
    dependencies=[Depends(AuthorizedRequest(role=Roles.ADMIN))],
)
async def reject_game_change_request(
    request_id: int,
    session: AsyncSession = Depends(get_session),
    s3_client: S3Client = Depends(get_s3_client)
):
    try:
        game_change_request = await disapprove_game_change_request(session, request_id)
        blob_s3_key = game_change_request.changes['game_img_url'].split('/')[2]
        await s3_client.delete_object(Bucket=settings.aws.bucket_name, Key=blob_s3_key)
    except ChangeRequestNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game change request not found",
        )
    except ChangeRequestNotPending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Game change request is not pending",
        )

    return GameChangeRequestResponseModel.from_orm(game_change_request)


@admins_router.get(
    "/me/moderator-requests",
    dependencies=[Depends(AuthorizedRequest(role=Roles.ADMIN))],
    response_model=List[GameChangeRequestResponseModel],
)
async def get_recent_game_change_requests(session: AsyncSession = Depends(get_session)):
    return await get_game_change_requests(session)


@admins_router.get(
    "/me/steam-guard-requests",
    dependencies=[Depends(AuthorizedRequest(role=Roles.ADMIN))],
    response_model=List[SteamGuardPendingRequestResponse],
)
async def fetch_pending_requests(
    limit: int = 50,
    redis_client: Redis = Depends(
        get_redis_client,
    ),
):
    pending_requests: List[SteamGuardPendingRequestResponse] = []

    async for key in async_islice(
        redis_client.scan_iter(f"{SG_REQUEST_PREFIX}:*"), limit
    ):
        raw_value = await redis_client.get(key)
        if not raw_value:
            continue

        if (
            SteamGuardRequestStatus.model_validate_json(raw_value).status
            == SteamGuardStatus.COMPLETED
        ):
            continue

        pending_request = SteamGuardPendingRequestResponse.model_validate_json(
            raw_value
        )
        pending_request.request_id = get_id_from_common_redis_key(key)

        pending_requests.append(pending_request)

    return pending_requests


@admins_router.post(
    "/me/steam-guard-requests/{request_id}",
    dependencies=[Depends(AuthorizedRequest(role=Roles.ADMIN))],
)
async def set_code(
    request_id: str,
    request: SetSteamGuardCodeRequest,
    redis_client: Redis = Depends(get_redis_client),
):
    key = generate_common_redis_key(SG_REQUEST_PREFIX, request_id)

    exists = await redis_client.exists(key)
    if not exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No steam code requests found for such id",
        )

    complete_request = SteamGuardSetModel(
        status=SteamGuardStatus.COMPLETED, code=request.code
    )

    await redis_client.set(key, complete_request.model_dump_json(), ex=10800)  # 3 hours
