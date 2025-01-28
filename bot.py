import asyncio
from aiogram import Bot, Dispatcher
import logging
from handlers import router
from config import BOT_TOKEN
from middlewares import LoggingMiddleware
from utils import set_commands

logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=BOT_TOKEN)
# Диспетчер
dp = Dispatcher()
dp.include_router(router)
# Настраиваем middleware и обработчики
dp.message.middleware(LoggingMiddleware())

async def main():
    print('Бот запущен')
    await set_commands(bot)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())