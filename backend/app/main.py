import time
import uuid
from typing import Callable

import uvicorn
from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette import status
from starlette.responses import JSONResponse

from app.api.admin import admins_router
from app.api.auth_flow import login_router, register_router
from app.api.game import games_router
from app.api.game_account import game_accounts_router, steam_guard_router
from app.api.purchases import payment_router, rental_router
from app.api.user import users_router
from app.business_logic.exceptions import (AuthenticationError,
                                           AuthorizationError)
from app.logger import logger

app = FastAPI()

api_v1 = APIRouter(prefix="/api/v1")
api_v1.include_router(login_router)
api_v1.include_router(register_router)
api_v1.include_router(games_router)
api_v1.include_router(users_router)
api_v1.include_router(admins_router)
api_v1.include_router(game_accounts_router)
api_v1.include_router(rental_router)
api_v1.include_router(payment_router)
api_v1.include_router(steam_guard_router)

app.include_router(api_v1)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-MFA-Required"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Callable):
    request.req_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    response = await call_next(request)

    process_time = time.perf_counter() - start_time
    logger.info(
        "request processed",
        latency=str(process_time),
        client_ip=request.client.host,
        path=request.url.path,
        method=request.method,
        req_id=request.req_id,
    )
    return response


@app.exception_handler(AuthenticationError)
async def http_exception_handler(request: Request, exc: AuthenticationError):
    logger.info("got AuthenticationError exception", req_id=getattr(request, "req_id", None))  # type: ignore
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token or expired token.",
    )


@app.exception_handler(AuthorizationError)
async def http_exception_handler(request: Request, exc: AuthorizationError):
    logger.info("got AuthorizationError exception", req_id=getattr(request, "req_id", None))  # type: ignore
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="Access forbidden."
    )


@app.exception_handler(Exception)
async def http_exception_handler(request: Request, exc: Exception):
    logger.opt(exception=exc).info("got unexpected exception", req_id=getattr(request, "req_id", None))  # type: ignore
    # return JSONResponse(
    #     content="Error has occurred on a server side",
    #     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    # )
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error has occurred on a server side"
    )


if __name__ == "__main__":
    uvicorn.run(app, port=8080)
