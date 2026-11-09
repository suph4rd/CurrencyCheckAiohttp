from app.core.i18n import gettext


class RateServiceError(Exception):
    code = "invalid_provider_response"
    message = gettext("Invalid provider response!")
    status = 400


class InvalidProviderResponse(RateServiceError):
    pass


class ProviderUnavailable(RateServiceError):
    code = "provider_unavailable"
    message = gettext("Could not connect to the provider!")
    status = 417


class ProviderTimeout(ProviderUnavailable):
    code = "provider_timeout"
    message = gettext("The provider request timed out!")


class DatabaseSaveError(RateServiceError):
    code = "database_save_failed"
    message = gettext("Could not save data to the database!")
