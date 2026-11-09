from aiohttp import web

from . import api, views
from app.core.settings import STATIC_PATH


def setup_routes(app: web.Application) -> None:
    app.router.add_static("/static/", STATIC_PATH, name="static")
    app.router.add_post('/preferences/language', views.set_language, name="set_language")
    app.router.add_get('/', views.main_page, name="main")
    app.router.add_view('/belarusbank-view/', views.BelarusbankBankTemplateView, name="belarusbank_view")
    app.router.add_view('/myfin-view/', views.MyfinBankTemplateView, name="myfin_view")
    app.router.add_view('/api/belarusbank-view/', api.BelarusbankBankApi, name="belarusbank_api_view")
    app.router.add_view('/api/myfin-view/', api.MyfinBankApi, name="myfin_api_view")
