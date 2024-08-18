import asyncio
from aiogram import Bot
from database import SQL
from decimal import Decimal
from aiohttp import ClientSession
from string_objects import strip_decimal
from config import COINMARKETCAP_API_KEY


async def check_prices(bot: Bot):
    while True:  # Бесконечный цикл для постоянной проверки цен
        async with SQL() as db:
            records = await db.get_thresholds()  # Получение записей, содержащих пороговые значения для криптовалют

        for record in records:  # Проход по каждой записи из базы данных
            currency = record['currency']  # Извлечение символа валюты из текущей записи
            async with ClientSession() as session:  # Создание асинхронной сессии для HTTP-запросов
                async with session.get(
                        f"https://pro-api.coinmarketcap.com/v1"
                        f"/cryptocurrency/quotes/latest?symbol={currency}&convert=USD",
                        headers={'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY}) as response:
                    # Выполнение запроса к CoinMarketCap API для получения текущей цены криптовалюты
                    data = await response.json()  # Декодирование ответа в JSON

            price = Decimal(str(data['data'][currency]['quote']['USD']['price']))
            # Получение цены из JSON и преобразование её в Decimal
            price_text = str(price).rstrip('0').rstrip('.')  # Убираем нули после запятой, для красивого вывода

            if price <= record['min_value']:  # Проверка, если цена ниже установленного минимального значения
                text = (f"Цена <b>{currency}</b> упала ниже "
                        f"<b>{strip_decimal(record['min_value'])} USD</b> и составляет <b>{price_text} USD</b>.")

                await bot.send_message(
                    chat_id=record['user_id'],  # Идентификатор пользователя, которому нужно отправить сообщение
                    text=text, parse_mode='HTML')  # Отправка сообщения пользователю через Telegram

            elif price >= record['max_value']:  # Проверка, если цена выше установленного максимального значения
                text = (f"Цена <b>{currency}</b> превысила "
                        f"<b>{strip_decimal(record['max_value'])} USD</b> и составляет <b>{price_text} USD</b>.")

                await bot.send_message(
                    chat_id=record['user_id'],  # Идентификатор пользователя
                    text=text,
                    parse_mode='HTML')  # Отправка сообщения пользователю через Telegram
        await asyncio.sleep(max(300 * len(records), 30))  # Из расчёта на 10000 запросов в месяц
