from enum import Enum


class EnumMixin:
    @staticmethod
    def get_dict() -> dict:
        return {item.name: item.value for item in CurrencyEnum.__members__.values()}


class CurrencyEnum(EnumMixin, Enum):
    USD_buy = "USD Покупка"
    USD_sell = "USD Продажа"
    EUR_buy = "EUR Покупка"
    EUR_sell = "EUR Продажа"
    RUB_buy = "100RUB Покупка"
    RUB_sell = "100RUB Продажа"
    EUR_USD_buy = "EUR->USD Покупка"
    EUR_USD_sell = "EUR->USD Продажа"
