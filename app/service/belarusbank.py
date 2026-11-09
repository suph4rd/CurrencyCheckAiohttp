from app.core.constants import BELARUSBANK_URL
from app.service.base import BaseRateService


class BelarusbankService(BaseRateService):
    url = BELARUSBANK_URL
    prefix = "belarusbank"
