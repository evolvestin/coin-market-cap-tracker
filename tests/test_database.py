import pytest
from database import SQL
from decimal import Decimal


@pytest.mark.asyncio
async def test_create_table():
    async with SQL() as db:
        result = await db.connection.fetch(
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'thresholds';"
        )
        assert len(result) == 1


@pytest.mark.asyncio
async def test_delete_all_thresholds():
    user_rows = []
    async with SQL() as db:
        await db.add_threshold(123456, 'BTC', Decimal('30000.0'), Decimal('40000.0'))
        await db.add_threshold(123456, 'ETH', Decimal('1500.0'), Decimal('2500.0'))
        await db.delete_all_thresholds(123456)
        rows = await db.get_thresholds()
        for record in rows:
            user_rows.append(record) if record['user_id'] == 123456 else None
        assert len(user_rows) == 0


@pytest.mark.asyncio
async def test_add_threshold():
    user_rows = []
    async with SQL() as db:
        rows_before = await db.get_thresholds()

    async with SQL() as db:
        await db.add_threshold(123456, 'BTC', Decimal('30000.0'), Decimal('40000.0'))
        rows_after = await db.get_thresholds()
        await db.delete_threshold_by_currency(123456, 'BTC')

    for record in rows_after:
        user_rows.append(record) if record['user_id'] == 123456 else None
    assert len(rows_before) + 1 == len(rows_after)
    assert user_rows[0]['user_id'] == 123456
    assert user_rows[0]['currency'] == 'BTC'
    assert user_rows[0]['min_value'] == Decimal('30000.0')
    assert user_rows[0]['max_value'] == Decimal('40000.0')


@pytest.mark.asyncio
async def test_delete_threshold_by_currency():
    user_rows = []
    async with SQL() as db:
        await db.add_threshold(123456, 'TRX', Decimal('0.10'), Decimal('0.20'))
        await db.delete_threshold_by_currency(123456, 'TRX')
        rows = await db.get_thresholds()
    for record in rows:
        user_rows.append(record) if record['user_id'] == 123456 and record['currency'] == 'TRX' else None
    assert len(user_rows) == 0
