from typing import Optional, Any
from aiohttp.web_exceptions import HTTPBadRequest, HTTPException


class HTTPErrorMixin(HTTPException):
    text: Optional[str] = None

    def __init__(
            self,
            *args,
            **kwargs,
    ) -> None:
        if not kwargs.get("text"):
            kwargs["text"] = self.text
        super().__init__(
            *args,
            **kwargs
        )


class HandleError(HTTPErrorMixin, HTTPBadRequest):
    text = "Ошибка распаковки ответа!"


class DatabaseSaveError(HTTPErrorMixin, HTTPBadRequest):
    text = "Ошибка записи объекта в базу данных!"
