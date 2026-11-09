from functools import lru_cache

from babel.support import Translations

from app.core.settings import BASE_DIR


def gettext(message: str) -> str:
    """Mark a message for extraction without translating globally."""
    return message


@lru_cache(maxsize=2)
def translations(locale: str):
    return Translations.load(BASE_DIR / 'locales', locales=[locale])


