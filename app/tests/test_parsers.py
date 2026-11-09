import unittest
from pathlib import Path

from app.service.parsers import MyfinParser


TABLE_START = '<table class="currencies-courses--bordered"><tbody class="sort_body">'
TABLE_END = '</tbody></table>'
ROW_START = '<tr class="currencies-courses__row-main" data-row-type="default">'
RATE_CELL = '<td class="currencies-courses__currency-cell">{}</td>'


def bank_table(name='<span>Test Bank</span>', rates=('1', '2', '3', '4', '5', '6')):
    return (TABLE_START + ROW_START + f'<td>{name}</td>'
            + ''.join(RATE_CELL.format(rate) for rate in rates)
            + '</tr>' + TABLE_END)


class MyfinParserTests(unittest.TestCase):
    def test_current_fixture(self):
        html = (Path(__file__).parent / 'fixtures' / 'myfin_current.html').read_text(encoding='utf-8')
        expected = []
        for name, rates in (
            ('Альфа Банк', ('2.935', '2.97', '3.27', '3.3', '3.4767', '3.665')),
            ('Банк БелВЭБ', ('2.92', '2.965', '3.25', '3.35', '3.46', '3.68')),
            ('СтатусБанк', ('2.948*', '2.948', '3.282', '3.282', '3.4767', '3.625')),
        ):
            item = {key: value for key, value in zip(
                ('USD_buy', 'USD_sell', 'EUR_buy', 'EUR_sell', 'RUB_buy', 'RUB_sell'), rates)}
            item.update(name=name, EUR_USD_buy=None, EUR_USD_sell=None)
            expected.append(item)
        self.assertEqual(MyfinParser(html)(), expected)

    def test_missing_table(self):
        with self.assertRaisesRegex(ValueError, 'table is missing'):
            MyfinParser('<html></html>')()

    def test_empty_table(self):
        with self.assertRaisesRegex(ValueError, 'table is empty'):
            MyfinParser(TABLE_START + TABLE_END)()

    def test_incomplete_row(self):
        for html in (bank_table(rates=('1', '2')), TABLE_START + ROW_START + '</tr>' + TABLE_END):
            with self.subTest(html=html), self.assertRaisesRegex(ValueError, 'row is incomplete'):
                MyfinParser(html)()

    def test_empty_rate(self):
        for rate in ('', '   '):
            with self.subTest(rate=rate), self.assertRaisesRegex(ValueError, 'row is incomplete'):
                MyfinParser(bank_table(rates=(rate, '2', '3', '4', '5', '6')))()

    def test_fallback_bank_name(self):
        for name in ('', '<span></span>', '<span>   </span>', 'Name without span'):
            with self.subTest(name=name):
                result = MyfinParser(bank_table(name=name))()
                self.assertEqual(result[0]['name'], '')
                self.assertEqual(result[0]['USD_buy'], '1')
