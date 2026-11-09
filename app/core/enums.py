from enum import Enum
from collections.abc import Callable

from app.core.i18n import gettext


class CurrencyEnum(Enum):
    USD_buy = gettext("USD Buy")
    USD_sell = gettext("USD Sell")
    EUR_buy = gettext("EUR Buy")
    EUR_sell = gettext("EUR Sell")
    RUB_buy = gettext("100RUB Buy")
    RUB_sell = gettext("100RUB Sell")
    EUR_USD_buy = gettext("EUR->USD Buy")
    EUR_USD_sell = gettext("EUR->USD Sell")

    @classmethod
    def get_dict(cls, translator: Callable[[str], str]) -> dict[str, str]:
        return {item.name: translator(item.value) for item in cls}
