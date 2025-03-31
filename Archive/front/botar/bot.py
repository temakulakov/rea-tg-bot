import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.client.bot import DefaultBotProperties
from config import BOT_TOKEN, REDIS_DSN
from handlers.start import router as start_router
from handlers.speaker import router as speaker_router
from handlers.chaperone import router as chaperone_router
from handlers.workshops import router as workshops_router
from handlers.commands import router as commands_router

# Настройка логирования – всегда включено
logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default_bot_properties=DefaultBotProperties(parse_mode="Markdown")
    )
    storage = RedisStorage.from_url(REDIS_DSN, state_ttl=None, data_ttl=None)
    dp = Dispatcher(storage=storage)
    dp.include_router(start_router)
    dp.include_router(commands_router)
    dp.include_router(speaker_router)
    dp.include_router(chaperone_router)
    dp.include_router(workshops_router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
