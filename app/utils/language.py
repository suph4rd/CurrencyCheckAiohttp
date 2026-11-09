import re

from app.core.constants import SUPPORTED_LANGUAGES

_RANGE = re.compile(r'^(?:[a-zA-Z]{1,8}(?:-[a-zA-Z0-9]{1,8})*|\*)$')
_WEIGHT = re.compile(r'^(?:0(?:\.\d{0,3})?|1(?:\.0{0,3})?)$')
def select_language(cookie: str | None, accept_language: str = '') -> str:
    if cookie in SUPPORTED_LANGUAGES:
        return cookie
    preferences = []
    for index, entry in enumerate(accept_language.split(',')):
        parts = [part.strip() for part in entry.split(';')]
        language = parts[0].lower()
        if not _RANGE.fullmatch(language) or len(parts) > 2:
            continue
        weight = 1.0
        if len(parts) == 2:
            key, separator, value = parts[1].partition('=')
            if key.lower() != 'q' or not separator or not _WEIGHT.fullmatch(value):
                continue
            weight = float(value)
        preferences.append((language, weight, index))
    banned = {language for language, weight, _ in preferences if weight == 0}
    for language, weight, _ in sorted(preferences, key=lambda item: (-item[1], item[2])):
        if not weight:
            continue
        candidates = SUPPORTED_LANGUAGES if language == '*' else (language.split('-')[0],)
        for candidate in candidates:
            if (candidate in SUPPORTED_LANGUAGES and language not in banned
                    and (candidate not in banned or '-' in language)):
                # An explicit preference takes precedence over a wildcard exclusion.
                if '*' not in banned or language != '*':
                    return candidate
    return 'ru'


