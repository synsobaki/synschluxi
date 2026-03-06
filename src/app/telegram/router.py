from aiogram import Router

from src.app.telegram.handlers import router as handlers_router


def setup_router() -> Router:
    router = Router()
    router.include_router(handlers_router)
    return router