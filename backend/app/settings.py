import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic.utils import deep_update
from yaml import safe_load

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))

# be aware that the lower is file the higher priority of override it has,
# it means that duplicate fields from config will be overridden from secrets
config_files = [
    Path(ROOT_DIR, "config.yml"),
    Path(ROOT_DIR, "secrets.yml"),
]


class DatabaseSettings(BaseModel):
    host: str
    user: str
    password: str
    name: str

    @property
    def url(self):
        return "mysql+asyncmy://{}:{}@{}/{}".format(
            self.user,
            self.password,
            self.host,
            self.name,
        )


class AwsSettings(BaseModel):
    url: str
    access_key_id: str
    secret_access_key: str
    bucket_name: str
    region_name: str


class RedisSettings(BaseModel):
    host: str
    port: int
    password: str


class EmailSenderSettings(BaseModel):
    host: str
    port: int
    user: str
    password: str


class StripeSettings(BaseModel):
    secret_key: str


class AuthSettings(BaseModel):
    secret: str


class FrontendSettings(BaseModel):
    url: str


class Settings(BaseModel):
    database: DatabaseSettings
    redis: RedisSettings
    email_sender: EmailSenderSettings
    frontend: FrontendSettings
    stripe: StripeSettings
    auth: AuthSettings
    aws: AwsSettings


def config_file_settings() -> dict[str, Any]:
    config: dict[str, Any] = {}
    for path in config_files:
        if not path.is_file():
            print(f"No file found at `{path.resolve()}`")
            continue
        print(f"Reading config file `{path.resolve()}`")
        if path.suffix in {".yaml", ".yml"}:
            config = deep_update(config, load_yaml(path))
        else:
            print(f"Unknown config file extension `{path.suffix}`")
    return config


def load_yaml(path: Path) -> dict[str, Any]:
    with Path(path).open("r") as f:
        config = safe_load(f)
    if not isinstance(config, dict):
        raise TypeError(f"Config file has no top-level mapping: {path}")
    return config


settings = Settings(**config_file_settings())  # type: ignore
