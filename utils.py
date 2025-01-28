from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault

async def set_commands(bot: Bot):

    commands = [
        BotCommand(command="/start", description="Начало работы с ботом"),
        BotCommand(command="/help", description="Показать все доступные команды"),
        BotCommand(command="/set_profile", description="Начать создание профиля"),
        BotCommand(command="/view_profiles", description="Посмотреть созданные профили"),
        BotCommand(command="/log_water", description="Добавить объём выпитой воды"),
        BotCommand(command="/log_food", description="Добавить съеденные калории"),
        BotCommand(command="/log_activity", description="Добавить тренировку"),
        BotCommand(command="/check_progress", description="Показать прогресс"),
        BotCommand(command="/plot_progress", description="Показать прогресс на графике"),
        BotCommand(command="/delete", description="Отменить последнюю запись"),
    ]
    await bot.set_my_commands(commands, BotCommandScopeDefault())