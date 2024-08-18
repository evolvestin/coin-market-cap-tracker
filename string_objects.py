from decimal import Decimal


def strip_decimal(value: Decimal) -> str:
    return '{:f}'.format(value).rstrip('0').rstrip('.')  # Форматирование в строку, удаление конечных нулей и точки
