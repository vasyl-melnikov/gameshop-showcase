from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from app.business_logic.auth import verify_token_access
from app.dto_schemas.auth import Roles, TokenData
from app.logger import logger

SG_REQUEST_PREFIX = "steam_guard_request"
TEMP_USER_CODE_REQUEST_PREFIX = "temp_user_code_request"


class AuthorizedRequest(HTTPBearer):
    def __init__(self, role: Roles, exact_role: bool = False):
        self.role = role
        self.exact_role = exact_role
        super(AuthorizedRequest, self).__init__()

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials | None = await super(
            AuthorizedRequest, self
        ).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme.",
                )
            token_data = verify_token_access(
                credentials.credentials, role=self.role, exact_role=self.exact_role
            )
            request.token_data = token_data  # type: ignore
            return credentials.credentials
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization code.",
            )


def get_token_data(request: Request) -> TokenData:
    try:
        token_data = request.token_data  # type: ignore
    except Exception:
        raise Exception("Token data cannot is not present in the request ")

    yield token_data


def get_logger(request: Request) -> logger:
    log_context = {
        "client_ip": request.client.host,
        "path": request.url.path,
        "method": request.method,
        "req_id": getattr(request, "req_id", None),  # type: ignore
    }

    yield logger.bind(**log_context)


def generate_common_redis_key(prefix: str, identifier: str) -> str:
    # Must include unique for each responsibility prefix and unique identifier
    return f"{prefix}:{identifier}"


def get_id_from_common_redis_key(key: bytes) -> str:
    return key.decode().split(":")[1]
