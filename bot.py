import asyncio
from aiogram import Bot, Dispatcher
import logging
from aiohttp import web
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

async def run_bot():
    print('Бот запущен')
    await set_commands(bot)
    await dp.start_polling(bot)

async def handle(request):
    return web.Response(text="Bot is running!")

def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    return app

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(run_bot())

    web.run_app(start_web_server(), host='0.0.0.0', port=3000)