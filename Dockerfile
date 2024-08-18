# Используем официальный Python образ в качестве базового
FROM python:3.10-slim

# Устанавливаем зависимости
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# Указываем команду для запуска приложения
CMD ["python", "main.py"]