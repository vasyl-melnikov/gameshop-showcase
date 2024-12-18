from typing import AsyncGenerator

import aioboto3
from types_aiobotocore_s3.client import S3Client

from app.settings import settings

session = aioboto3.Session(aws_access_key_id=settings.aws.access_key_id, aws_secret_access_key=settings.aws.secret_access_key)


async def get_s3_client() -> AsyncGenerator[S3Client, None]:
    async with session.client("s3", endpoint_url=settings.aws.url, region_name=settings.aws.region_name) as s3:
        yield s3
