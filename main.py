import logging

from fastapi.responses import RedirectResponse
from nicegui import app, run, ui

from auth import is_admin
from config import APP_PORT, AUTO_INIT_DB, STORAGE_SECRET
from db.connection import get_connection, get_user_by_id, init_pool
from pages import admin_page, board_page, dashboard_page, login_page, team_page, tour
from pages.ui_kit import app_shell, install_theme
from scripts.init_db import ensure_schema

install_theme()
tour.install()


def is_logged_in():
    return app.storage.user.get("user_id") is not None


def log_out():
    app.storage.user.clear()
    ui.navigate.to("/login")


def load_user(user_id):
    """The user's row; None when the account no longer exists. Raises on DB errors."""
    conn = get_connection()
    try:
        return get_user_by_id(conn, user_id)
    finally:
        conn.close()


async def authed_page(active, render, tour_requested=False):
    """
    Common guard and shell for every screen behind the login.
    The page is sent right away; the database work happens after the browser connects,
    in a worker thread, so a slow query never freezes the server for other users.
    """
    if not is_logged_in():
        return RedirectResponse("/login")
    user_id = app.storage.user["user_id"]  # session storage is only reachable here, not in worker threads
    await ui.context.client.connected(timeout=30)
    try:
        user = await run.io_bound(load_user, user_id)
    except Exception as e:
        logging.exception("Loading the current user failed")
        ui.label(f"שגיאת תקשורת עם מסד הנתונים: {e}").classes("warn-text p-8")
        return None
    if user is None:
        # Account was deleted while this browser was still logged in
        app.storage.user.clear()
        ui.navigate.to("/login")
        return None
    admin = is_admin(user["Username"])
    if active == "admin" and not admin:
        ui.navigate.to("/")
        return None
    with app_shell(active, user["Username"], show_admin=admin, on_logout=log_out):
        await render(user["ID"])
    if active in tour.STEPS:
        # the dashboard opens the tour by itself once per user; other screens continue it on request
        first_visit = active == "dashboard" and not user["Tour_Done"]
        tour.attach(active, user["ID"], start=tour_requested or first_visit)
    return None


@ui.page("/login")
def login():
    if is_logged_in():
        return RedirectResponse("/")
    login_page.build("login")


@ui.page("/signup")
def signup():
    if is_logged_in():
        return RedirectResponse("/")
    login_page.build("signup")


@ui.page("/")
async def index(tour: str = None):
    return await authed_page("dashboard", dashboard_page.build, tour_requested=bool(tour))


@ui.page("/board")
async def board(week: str = None, tour: str = None):
    return await authed_page("board", lambda user_id: board_page.build(user_id, week), tour_requested=bool(tour))


@ui.page("/team")
async def team(tab: str = "people", tour: str = None):
    return await authed_page("team", lambda user_id: team_page.build(user_id, tab), tour_requested=bool(tour))


@ui.page("/admin")
async def admin():
    async def render(user_id):
        admin_page.build(user_id)
    return await authed_page("admin", render)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.on_startup
def on_startup():
    if AUTO_INIT_DB:
        try:
            ensure_schema()
        except Exception as exc:
            print(f"[WARN] Startup database verification: {exc}")
    try:
        init_pool()
    except Exception as exc:
        print(f"[WARN] Could not open the database connection pool yet: {exc}")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="שיבוץ משמרות",
        host="0.0.0.0",
        port=APP_PORT,
        reload=False,
        show=False,
        forwarded_allow_ips="*",
        storage_secret=STORAGE_SECRET,
    )
