import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand, ErrorEvent

from config import load_config
from database import Database
from handlers import get_routers
from middlewares.maintenance import MaintenanceMiddleware
from middlewares.subscription import SubscriptionMiddleware
from middlewares.user_tracker import UserTrackerMiddleware
from services.backup import auto_backup_loop
from utils.logger import setup_logging

log = logging.getLogger(__name__)


async def on_error(event: ErrorEvent) -> bool:
    log.error("Handlerda xato: %s", event.exception, exc_info=event.exception)
    return True


async def start_health_server(port: int) -> web.AppRunner:
    """Render/Railway kabi hostinglar uchun: PORT berilsa oddiy 'OK' sahifa ochadi
    (uptime monitor shu manzilni tekshiradi)."""
    app = web.Application()

    async def ok(_: web.Request) -> web.Response:
        return web.Response(text="OK")

    app.router.add_get("/", ok)
    app.router.add_get("/health", ok)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", port).start()
    log.info("Health-server ishga tushdi: port %s", port)
    return runner


async def main() -> None:
    config = load_config()
    setup_logging(config.logs_dir)

    db = Database(config.db_path)
    await db.init(config.admin_ids)

    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=None))
    dp = Dispatcher()
    dp["db"] = db
    dp["config"] = config

    # Middleware tartibi: foydalanuvchini saqlash -> texnik xizmat -> majburiy obuna
    for observer in (dp.message, dp.callback_query):
        observer.outer_middleware(UserTrackerMiddleware(db))
        observer.outer_middleware(MaintenanceMiddleware(db))
        observer.outer_middleware(SubscriptionMiddleware(db))

    for router in get_routers():
        dp.include_router(router)
    dp.errors.register(on_error)

    backup_task = asyncio.create_task(auto_backup_loop(bot, db, config.admin_ids))
    health_runner = await start_health_server(config.port) if config.port else None
    try:
        await bot.set_my_commands([BotCommand(command="start", description="Bosh sahifa")])
        await bot.delete_webhook(drop_pending_updates=False)
        me = await bot.get_me()
        log.info("Bot ishga tushdi: @%s", me.username)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        backup_task.cancel()
        await bot.session.close()
        if health_runner:
            await health_runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        log.info("Bot to'xtatildi")
