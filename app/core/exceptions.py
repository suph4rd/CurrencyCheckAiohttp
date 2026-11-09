class RateServiceError(Exception):
    code = "invalid_provider_response"
    message = "Ошибка распаковки ответа!"
    status = 400


class InvalidProviderResponse(RateServiceError):
    pass


class ProviderUnavailable(RateServiceError):
    code = "provider_unavailable"
    message = "Ошибка подключения к серверу!"
    status = 417


class ProviderTimeout(ProviderUnavailable):
    code = "provider_timeout"
    message = "Превышено время ожидания ответа сервера!"


class DatabaseSaveError(RateServiceError):
    code = "database_save_failed"
    message = "Ошибка записи объекта в базу данных!"
