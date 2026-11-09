from bs4 import BeautifulSoup, Tag

from app.core.constants import (MYFIN_TABLE_SELECTOR, MYFIN_ROW_SELECTOR,
                           MYFIN_CELL_SELECTOR, CURRENCY_KEYS)


class MyfinParser:
    def __init__(self, html: str) -> None:
        self.html = html

    def __call__(self) -> list[dict[str, str | None]]:
        handled_answer = [self._parse_bank_row(row) for row in self._find_bank_rows()]
        if not handled_answer:
            raise ValueError("Myfin currency table is empty")
        return handled_answer

    def _find_bank_rows(self) -> list[Tag]:
        soup = BeautifulSoup(self.html, 'html.parser')
        banks_body = soup.select_one(MYFIN_TABLE_SELECTOR)
        if banks_body is None:
            raise ValueError("Myfin currency table is missing")
        return list(banks_body.select(MYFIN_ROW_SELECTOR))

    def _parse_bank_row(self, bank_tr: Tag) -> dict[str, str | None]:
        bank_item: dict[str, str | None] = {"EUR_USD_buy": None, "EUR_USD_sell": None}
        cells = bank_tr.find_all("td", recursive=False)
        currency_cells = bank_tr.select(MYFIN_CELL_SELECTOR)
        if not cells or len(currency_cells) != len(CURRENCY_KEYS):
            raise ValueError("Myfin currency row is incomplete")
        bank_item["name"] = self._get_bank_name(cells[0])
        for key, cell in zip(CURRENCY_KEYS, currency_cells):
            value = cell.get_text(strip=True)
            if not value:
                raise ValueError("Myfin currency row is incomplete")
            bank_item[key] = value
        return bank_item

    def _get_bank_name(self, cell: Tag) -> str:
        name = cell.find("span", recursive=False)
        return name.get_text(" ", strip=True) if name else ""
