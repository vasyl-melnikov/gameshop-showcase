from typing import Optional

from pydantic import BaseModel, EmailStr

from app.dto_schemas.auth import Roles
from app.dto_schemas.validatiors import Password


class UserBase(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    email: EmailStr


class EmailOnlyUser(BaseModel):
    email: EmailStr


class PasswordOnlyUser(BaseModel):
    password: Password


class UserRole(BaseModel):
    role: Roles


class UserRolePatch(EmailOnlyUser, UserRole): ...


class UserCreate(UserBase, PasswordOnlyUser): ...


class UserLogin(BaseModel):
    email: EmailStr
    password: Password


class UserChangePassword(BaseModel):
    old_password: Password
    new_password: Password


class UserChangeEmail(EmailOnlyUser): ...


class UserResetPassword(EmailOnlyUser): ...


class UserUpdatePersonalInfo(BaseModel):
    first_name: str
    last_name: str


class UserResponseModel(UserBase):
    ukey: str

    class Config:
        from_attributes = True


class UserRoleResponseModel(UserResponseModel):
    role: Roles
    mfa_enabled: bool

    class Config:
        from_attributes = True
