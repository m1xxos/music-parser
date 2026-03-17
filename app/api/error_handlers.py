import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

class ApiError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code; self.message = message; self.status_code = status_code

def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def handle_api_error(_: Request, exc: ApiError):
        logger.warning('api_error code=%s message=%s', exc.code, exc.message)
        return JSONResponse(status_code=exc.status_code, content={'error': {'code': exc.code, 'message': exc.message}})

    @app.exception_handler(Exception)
    async def handle_unhandled(_: Request, exc: Exception):
        logger.exception('unhandled_error: %s', exc)
        return JSONResponse(status_code=500, content={'error': {'code': 'INTERNAL_ERROR', 'message': 'Internal server error'}})
