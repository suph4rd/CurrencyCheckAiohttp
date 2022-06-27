from aiohttp import web

from . import views


def setup_routes(app: web.Application) -> None:
    app.router.add_view('/', views.MainPage)
    app.router.add_view('/belarusbank-view/', views.BelarusbankBankTemplateView)
