import asyncio
from aiogram.types import BotCommand, BotCommandScopeDefault
from loguru import logger
from bot.config import bot, admins, dispatcher
from bot.dao.database_middleware import DatabaseMiddlewareWithoutCommit, DatabaseMiddlewareWithCommit
from bot.dao.album_middleware import AlbumMiddleware
from bot.admin.admin import admin_router
from bot.user.user_router import user_router
from bot.user.catalog_router import catalog_router

# Функция, которая настроит командное меню (дефолтное для всех пользователей)
async def set_commands():
    commands = [BotCommand(command='start', description='Старт')]
    await bot.set_my_commands(commands, BotCommandScopeDefault())

# Функция, которая выполнится, когда бот запустится
async def start_bot():
    await set_commands()
    for admin_id in admins:
        try:
            await bot.send_message(admin_id, f'Я запущен🥳.')
        except:
            pass
    logger.info("Бот успешно запущен.")

# Функция, которая выполнится, когда бот завершит свою работу
async def stop_bot():
    try:
        for admin_id in admins:
            await bot.send_message(admin_id, 'Бот остановлен. За что?😔')
    except:
        pass
    logger.error("Бот остановлен!")

async def main():
    # Регистрация мидлварей
    dispatcher.update.middleware.register(DatabaseMiddlewareWithoutCommit())
    dispatcher.update.middleware.register(DatabaseMiddlewareWithCommit())
    dispatcher.message.middleware(AlbumMiddleware())

    # Регистрация роутеров
    dispatcher.include_router(catalog_router)
    dispatcher.include_router(user_router)
    dispatcher.include_router(admin_router)

    # Регистрация функций
    dispatcher.startup.register(start_bot)
    dispatcher.shutdown.register(stop_bot)

    # Запуск бота в режиме long polling
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())