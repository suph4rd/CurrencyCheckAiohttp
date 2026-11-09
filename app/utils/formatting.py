import re

from babel.numbers import get_decimal_symbol

_NUMBER = re.compile(r'^(\s*[+-]?\d+)([.,])(\d+)(.*)$', re.DOTALL)


def format_rate(value, locale: str = 'ru') -> str:
    if value is None or str(value).strip() in ('', '-', '—'):
        return '—'
    text = str(value)
    match = _NUMBER.fullmatch(text)
    if not match:
        return text
    whole, _, fraction, note = match.groups()
    return whole + get_decimal_symbol(locale) + fraction + note


