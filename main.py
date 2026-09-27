from fastapi.responses import RedirectResponse
from nicegui import app, ui

from auth import is_admin
from config import APP_PORT, AUTO_INIT_DB, STORAGE_SECRET
from db.connection import get_connection, get_user_by_id
from pages import admin_page, board_page, dashboard_page, login_page, team_page
from pages.ui_kit import app_shell, install_theme
from scripts.init_db import ensure_schema

install_theme()


def is_logged_in():
    return app.storage.user.get("user_id") is not None


def log_out():
    app.storage.user.clear()
    ui.navigate.to("/login")


def current_user():
    """The logged-in user's row; None when the account no longer exists. Raises on DB errors."""
    conn = get_connection()
    try:
        return get_user_by_id(conn, app.storage.user["user_id"])
    finally:
        conn.close()


def authed_page(active, render):
    """Common guard and shell for every screen behind the login."""
    if not is_logged_in():
        return RedirectResponse("/login")
    try:
        user = current_user()
    except Exception as e:
        ui.label(f"שגיאת תקשורת עם מסד הנתונים: {e}").classes("warn-text p-8")
        return None
    if user is None:
        # Account was deleted while this browser was still logged in
        app.storage.user.clear()
        return RedirectResponse("/login")
    admin = is_admin(user["Username"])
    if active == "admin" and not admin:
        return RedirectResponse("/")
    with app_shell(active, user["Username"], show_admin=admin, on_logout=log_out):
        render(user["ID"])
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
def index():
    return authed_page("dashboard", dashboard_page.build)


@ui.page("/board")
def board(week: str = None):
    return authed_page("board", lambda user_id: board_page.build(user_id, week))


@ui.page("/team")
def team(tab: str = "people"):
    return authed_page("team", lambda user_id: team_page.build(user_id, tab))


@ui.page("/admin")
def admin():
    return authed_page("admin", admin_page.build)


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
