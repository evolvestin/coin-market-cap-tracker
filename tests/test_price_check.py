import pytest
import asyncio
from main import bot
from database import SQL
from decimal import Decimal
from price_check import check_prices
from aioresponses import aioresponses
from config import TEST_USER_ID, TELEGRAM_API_TOKEN


@pytest.mark.asyncio
async def test_check_prices():
    async with SQL() as db:
        await db.add_threshold(TEST_USER_ID, 'BTC', Decimal('30000.0'), Decimal('40000.0'))

    with aioresponses() as mocked:
        # Мокируем запросы к CoinMarketCap API
        mocked.get(
            'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol=BTC&convert=USD',
            payload={
                'data': {
                    'BTC': {
                        'quote': {
                            'USD': {
                                'price': 20000.00
                            }
                        }
                    }
                }
            }
        )

        telegram_api_url = f'https://api.telegram.org/bot{TELEGRAM_API_TOKEN}/sendMessage'
        mocked.post(
            telegram_api_url,
            payload={
                'ok': True,
                'result': {
                    'message_id': 123,
                    'chat': {'id': TEST_USER_ID},
                    'text': 'Цена <b>BTC</b> упала ниже <b>30000 USD</b> и составляет <b>20000 USD</b>.'
                }
            }
        )

        # Запускаем функцию с таймаутом для предотвращения бесконечного цикла
        task = asyncio.create_task(check_prices(bot))
        await asyncio.sleep(1)
        task.cancel()  # Прекращаем выполнение

        try:
            await task  # Ожидаем завершения задачи после отмены
        except asyncio.CancelledError:
            pass  # Ожидаемое исключение при отмене задачи

        assert task.cancelled()  # Проверка, что задача действительно была отменена
        assert len(mocked.requests) >= 2  # Должно быть два запроса: один к CoinMarketCap, один к Telegram
        assert str(list(mocked.requests.keys())[1][1]) == telegram_api_url

        async with SQL() as db:
            await db.delete_threshold_by_currency(TEST_USER_ID, 'BTC')
