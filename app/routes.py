from aiohttp import web

from . import views
from .settings import STATIC_PATH


def setup_routes(app: web.Application) -> None:
    app.router.add_static("/static/", STATIC_PATH, name="static")
    app.router.add_view('/', views.MainPage, name="main")
    app.router.add_view('/belarusbank-view/', views.BelarusbankBankTemplateView, name="belarusbank_view")
    app.router.add_view('/myfin-view/', views.MyfinBankTemplateView, name="myfin_view")
    app.router.add_view('/api/belarusbank-view/', views.BelarusbankBankApi, name="belarusbank_api_view")
    app.router.add_view('/api/myfin-view/', views.MyfinBankApi, name="myfin_api_view")
