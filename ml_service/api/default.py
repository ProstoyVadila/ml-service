from fastapi import Request, Response, APIRouter, status

default_router = APIRouter()


@default_router.get("/")
async def main(request: Request) -> str:
    return request.app.title


@default_router.get("/healthcheck")
async def healthcheck() -> Response:
    return Response(status_code=status.HTTP_200_OK)


@default_router.get("/ready")
async def ready() -> Response:
    return Response(status_code=status.HTTP_200_OK)


@default_router.get("/startup")
async def startup() -> Response:
    return Response(status_code=status.HTTP_200_OK)
