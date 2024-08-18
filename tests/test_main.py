import pytest
from database import SQL
from decimal import Decimal
from aiogram import types, Bot
from config import TEST_USER_ID
from main import bot, set_threshold, delete_threshold, delete_all_thresholds_handler


@pytest.mark.asyncio
async def test_set_threshold():
    Bot.set_current(bot)
    async with SQL() as db:
        message = types.Message(text='/set_threshold BTC 30000.0 40000.3', chat=types.Chat(id=TEST_USER_ID))
        rows_before = await db.get_thresholds()

    await set_threshold(message)

    async with SQL() as db:
        rows_after = await db.get_thresholds()
        assert len(rows_before) + 1 == len(rows_after)
        assert rows_after[-1]['currency'] == 'BTC'
        await db.delete_threshold_by_currency(message.chat.id, 'BTC')


@pytest.mark.asyncio
async def test_delete_threshold():
    Bot.set_current(bot)
    message = types.Message(text='/delete_threshold BTC', chat=types.Chat(id=TEST_USER_ID))
    async with SQL() as db:
        await db.add_threshold(TEST_USER_ID, 'BTC', Decimal('30000.0'), Decimal('40000.0'))

    await delete_threshold(message)

    async with SQL() as db:
        rows = await db.connection.fetch(
            'SELECT * FROM thresholds WHERE user_id = $1 AND currency = $2;', message.chat.id, 'BTC'
        )
    assert len(rows) == 0


@pytest.mark.asyncio
async def test_delete_all_thresholds_handler():
    Bot.set_current(bot)
    message = types.Message(text='/delete_all_thresholds', chat=types.Chat(id=TEST_USER_ID))
    async with SQL() as db:
        await db.add_threshold(TEST_USER_ID, 'BTC', Decimal('30000.0'), Decimal('40000.0'))
        await db.add_threshold(TEST_USER_ID, 'ETH', Decimal('1500.0'), Decimal('2500.0'))

    await delete_all_thresholds_handler(message)

    async with SQL() as db:
        rows = await db.connection.fetch('SELECT * FROM thresholds WHERE user_id = $1;', message.chat.id)
    assert len(rows) == 0
