from aiogram import Router

from . import (by_code, check_sub, common, favorites, menu, movies, new_movies,
               search)
from .admin import (admins, backup, broadcast, movie_add, movie_manage, panel, settings,
                    stats_users, sub_admin)


def get_routers() -> list[Router]:
    """Tartib muhim: birinchi mos kelgan handler ishlaydi.

    1) /start, /admin (har qanday holatda)   2) admin routerlari (FSM holatlari)
    3) foydalanuvchi routerlari              4) kod qabul qiluvchi umumiy handler (eng oxirida)
    """
    return [
        common.router,
        panel.router, movie_add.router, movie_manage.router, stats_users.router,
        broadcast.router, sub_admin.router, admins.router, settings.router, backup.router,
        menu.router, check_sub.router, search.router, movies.router,
        favorites.router, new_movies.router,
        by_code.router,
    ]
