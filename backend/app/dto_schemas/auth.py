from enum import Enum

from pydantic import BaseModel, EmailStr


class Roles(str, Enum):
    PARTIALLY_LOGGED_IN = "partially_logged_in"
    USER = "user"
    SUPPORT_MODERATOR = "support_moderator"
    ADMIN = "admin"
    ROOT_ADMIN = "root_admin"


class TokenType(str, Enum):
    BEARER = "Bearer"


role_weight_mapping = {
    Roles.PARTIALLY_LOGGED_IN: 1,
    Roles.USER: 2,
    Roles.SUPPORT_MODERATOR: 3,
    Roles.ADMIN: 4,
    Roles.ROOT_ADMIN: 5,
}


class Token(BaseModel):
    access_token: str
    token_type: TokenType


class TokenData(BaseModel):
    ukey: str
    email: EmailStr
    role: Roles


class MFACode(BaseModel):
    code: str
