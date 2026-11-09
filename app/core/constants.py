BELARUSBANK_URL = "https://belarusbank.by/api/kursExchange?city=%D0%9C%D0%B8%D0%BD%D1%81%D0%BA"
MYFIN_URL = "https://myfin.by/currency/minsk"
HTTP_TOTAL_TIMEOUT = 15
HTTP_CONNECT_TIMEOUT = 5
MYFIN_TABLE_SELECTOR = "table.currencies-courses--bordered > tbody.sort_body"
MYFIN_ROW_SELECTOR = ':scope > tr.currencies-courses__row-main[data-row-type="default"]'
MYFIN_CELL_SELECTOR = ':scope > td.currencies-courses__currency-cell'
CURRENCY_KEYS = ("USD_buy", "USD_sell", "EUR_buy", "EUR_sell", "RUB_buy", "RUB_sell")

SUPPORTED_LANGUAGES = ('ru', 'en')
LANGUAGE_COOKIE = 'language'
