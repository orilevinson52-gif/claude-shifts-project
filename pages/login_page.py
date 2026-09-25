from nicegui import app, ui

from auth import RegistrationError, authenticate, register


def log_in(user_id, username):
    app.storage.user.update({"user_id": user_id, "username": username})
    ui.navigate.to("/")


def auth_card(title):
    with ui.column().classes("w-full items-center q-mt-xl"):
        ui.label("מערכת שיבוץ משמרות").classes("rc-title text-2xl")
        card = ui.card().classes("w-full q-pa-lg").style("max-width: 380px")
        with card:
            ui.label(title).classes("rc-heading text-lg")
    return card


def build_login():
    with auth_card("כניסה"):
        username_input = ui.input("שם משתמש").classes("w-full")
        password_input = ui.input("סיסמה", password=True).classes("w-full")

        def submit():
            try:
                user_id = authenticate(username_input.value, password_input.value)
            except Exception as e:
                ui.notify(f"שגיאת תקשורת עם מסד הנתונים: {e}", color="negative")
                return
            if user_id is None:
                ui.notify("שם משתמש או סיסמה שגויים", color="negative")
                return
            log_in(user_id, username_input.value.strip())

        password_input.on("keydown.enter", submit)
        ui.button("כניסה", color="primary", on_click=submit).classes("w-full q-mt-md")
        with ui.row().classes("w-full justify-center q-mt-sm text-sm"):
            ui.label("אין לך חשבון?")
            ui.link("להרשמה", "/signup")


def build_signup():
    with auth_card("הרשמה"):
        username_input = ui.input("שם משתמש").classes("w-full")
        password_input = ui.input("סיסמה (לפחות 8 תווים)", password=True).classes("w-full")
        confirm_input = ui.input("אימות סיסמה", password=True).classes("w-full")

        def submit():
            if password_input.value != confirm_input.value:
                ui.notify("הסיסמאות אינן תואמות", color="negative")
                return
            try:
                user_id = register(username_input.value, password_input.value)
            except RegistrationError as e:
                ui.notify(str(e), color="negative")
                return
            except Exception as e:
                ui.notify(f"שגיאת תקשורת עם מסד הנתונים: {e}", color="negative")
                return
            log_in(user_id, username_input.value.strip())

        confirm_input.on("keydown.enter", submit)
        ui.button("הרשמה", color="primary", on_click=submit).classes("w-full q-mt-md")
        with ui.row().classes("w-full justify-center q-mt-sm text-sm"):
            ui.label("כבר יש לך חשבון?")
            ui.link("לכניסה", "/login")
