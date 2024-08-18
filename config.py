import os
from dotenv import load_dotenv

load_dotenv()  # Загрузка переменных окружения из файла .env

DATABASE_URL = os.getenv('DATABASE_URL')  # Строка подключения к базе
TEST_USER_ID = int(os.getenv('TEST_USER_ID'))  # Telegram ID пользователя для тестов
TELEGRAM_API_TOKEN = os.getenv('TELEGRAM_API_TOKEN')  # Telegram API токен из переменных окружения
COINMARKETCAP_API_KEY = os.getenv('COINMARKETCAP_API_KEY')  # CoinMarketCap API токен из переменных окружения
