"""Handlers package."""

from aiogram import Router

from . import start, admin


def setup_routers() -> Router:
    """Setup all routers."""
    router = Router()

    # Include handlers
    router.include_router(start.router)
    router.include_router(admin.router)

    return router
