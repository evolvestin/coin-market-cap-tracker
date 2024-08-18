import re
import asyncio
import logging
from database import SQL
from decimal import Decimal
from aiogram.utils import executor
from price_check import check_prices
from config import TELEGRAM_API_TOKEN
from string_objects import strip_decimal
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware


logging.basicConfig(level=logging.INFO)  # Базовое логирование

bot = Bot(token=TELEGRAM_API_TOKEN)  # Инициализация бота
dispatcher = Dispatcher(bot)
dispatcher.middleware.setup(LoggingMiddleware())  # Добавление middleware для логирования


async def set_commands(user_id: int) -> None:
    bot_commands = {
        'set_threshold': 'Установить порог цен для валюты',
        'delete_threshold': 'Удалить порог цен для валюты',
        'delete_all_thresholds': 'Удалить все пороги цен',
    }
    scope_chat = types.BotCommandScopeChat(user_id)
    user_commands = await bot.get_my_commands(scope_chat)
    base_commands = [types.BotCommand(command, command_desc) for command, command_desc in bot_commands.items()]
    if user_commands != base_commands:
        await bot.set_my_commands(base_commands, scope_chat)  # Установка команд бота для конкретного пользователя


# Обработчик команд /start и /help
@dispatcher.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await set_commands(message.chat.id)  # Установка команд при старте или при вызове /help
    await message.reply('Привет! Я бот для отслеживания курса криптовалют.')


# Обработчик команды /delete_all_thresholds для удаления всех порогов цен
@dispatcher.message_handler(commands=['delete_all_thresholds'])
async def delete_all_thresholds_handler(message: types.Message):
    async with SQL() as db:
        await db.delete_all_thresholds(message.chat.id)  # Удаление всех порогов цен из базы

    await message.reply('Все пороговые значения удалены.')  # Ответ пользователю о завершении удаления


# Обработчик команды /delete_threshold для удаления порога цены
@dispatcher.message_handler(commands=['delete_threshold'])
async def delete_threshold(message: types.Message):
    args = re.sub(r'\s+', ' ', message.text).split()[1:]  # Очистка и разбивка текста на аргументы
    if len(args) < 1:  # Проверка на достаточность аргументов
        await message.reply('Использование: <code>/delete_threshold BTC</code>', parse_mode='HTML')
        return

    currency = args[0].upper()
    async with SQL() as db:
        await db.delete_threshold_by_currency(message.chat.id, currency)  # Удаление порога для указанной валюты

    await message.reply(f'Пороговые значения для <b>{currency}</b> удалены.', parse_mode='HTML')  # Ответ пользователю


# Обработчик команды /set_threshold для установки порога цены
@dispatcher.message_handler(commands=['set_threshold'])
async def set_threshold(message: types.Message):
    example = '<code>/set_threshold BTC 30000.0 40000.3</code>'
    if message.text == '/set_threshold':
        await message.reply(f'Использование: {example}', parse_mode='HTML')
        return

    args = re.sub(r'\s+', ' ', message.text).split()[1:]  # Очистка и разбивка текста на аргументы
    if len(args) >= 3:  # Проверка на достаточность аргументов
        if re.sub(r'\D', ' ', args[0]) and re.sub(r'\d', ' ', args[1]) and re.sub(r'\d', ' ', args[2]):
            # Преобразование строк в числа и удаление лишних символов
            min_value_str = re.sub(r'\.+', '.', re.sub(r'\D', '.', args[1])).strip('.')
            max_value_str = re.sub(r'\.+', '.', re.sub(r'\D', '.', args[2])).strip('.')

            currency = args[0].upper()
            min_value = Decimal(min_value_str)
            max_value = Decimal(max_value_str)
            async with SQL() as db:
                await db.add_threshold(message.chat.id, currency, min_value, max_value)  # Добавление порогов цен в базу
            text = (f'Установлены пороги для {currency}: '
                    f'<b>{strip_decimal(min_value)} — {strip_decimal(max_value)} USD</b>.')
        else:
            text = (f'Неверно указаны параметры. Команда пишется так:\n'
                    f'{example}')
    else:
        text = (f'Недостаточно параметров. Команда пишется так:\n'
                f'{example}')
    await message.reply(text, parse_mode='HTML')


async def on_startup(dp: Dispatcher):  # Функция, запускающая проверку цен при старте бота
    asyncio.create_task(check_prices(bot))  # noqa Запуск задачи для проверки цен


if __name__ == '__main__':
    executor.start_polling(dispatcher, on_startup=on_startup)  # Запуск бота
