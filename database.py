import asyncpg
from decimal import Decimal
from config import DATABASE_URL


class SQL:
    def __init__(self):
        self.connection = None
        self.transaction = None

    async def database_connect(self):
        self.connection = await asyncpg.connect(DATABASE_URL)  # Подключение к базе
        self.transaction = self.connection.transaction()

    async def __aenter__(self):
        await self.database_connect()  # Выполнение подключения к базе данных при входе в контекстный менеджер
        await self.transaction.start()  # Начало транзакции
        await self.create_table()  # Вызываем проверку существования таблицы
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.transaction.commit()
        if self.connection:
            await self.connection.close()  # Закрытие соединения при выходе из контекстного менеджера

    async def create_table(self):
        """Проверка наличия таблицы в базе; если её нет — создаём"""
        await self.connection.execute(
            'CREATE TABLE IF NOT EXISTS thresholds ('
            'id SERIAL PRIMARY KEY, user_id BIGINT, '
            'currency TEXT NOT NULL, min_value NUMERIC(24, 12), max_value NUMERIC(24, 12)'
            ');'
        )

    async def add_threshold(self, user_id: int, currency: str, min_value: Decimal, max_value: Decimal):
        """Добавление в базу порогового значения"""
        await self.connection.execute(
                'INSERT INTO thresholds(user_id, currency, min_value, max_value) VALUES($1, $2, $3, $4);',
                user_id, currency, min_value, max_value
            )

    async def get_thresholds(self) -> list:
        """Получение всех пороговых значений из базы"""
        rows = await self.connection.fetch('SELECT * FROM thresholds;')
        return rows

    async def delete_threshold_by_currency(self, user_id: int, currency: str):
        """Удаление порогового значения по названию валюты для конкретного пользователя"""
        await self.connection.execute(
                'DELETE FROM thresholds WHERE user_id = $1 AND currency = $2;', user_id, currency
            )

    async def delete_all_thresholds(self, user_id: int):
        """Удаление всех пороговых значений для конкретного пользователя"""
        await self.connection.execute('DELETE FROM thresholds WHERE user_id = $1;', user_id)
