from nicegui import app, run, ui

from auth import MIN_PASSWORD_LENGTH, RegistrationError, authenticate, register
from pages.ui_kit import apply_color_scheme, button, icon

ART = """
<div style="position:absolute;top:90px;right:70px;left:70px;display:flex;flex-direction:column;gap:14px">
  <div class="float-a" style="background:#fff;color:#1a1a17;border-radius:16px;padding:18px;display:flex;flex-direction:column;gap:12px;box-shadow:0 20px 50px rgba(0,0,0,.25)">
    <div style="display:flex;justify-content:space-between;align-items:center">
      <span style="font-family:Rubik,sans-serif;font-size:15px;font-weight:600">השבוע</span>
      <span style="font-size:12.5px;color:#1f7a55;font-weight:600">46/56 משובצות</span>
    </div>
    <div style="display:grid;grid-template-columns:84px repeat(5,minmax(0,1fr));gap:6px;font-size:12px">
      <span style="font-weight:600;align-self:center">שער ראשי</span>
      <span style="background:#e3f3eb;color:#1c6b4b;border-radius:6px;padding:8px 6px;font-weight:600">רועי</span>
      <span style="background:#e3f3eb;color:#1c6b4b;border-radius:6px;padding:8px 6px;font-weight:600">נועה</span>
      <span style="border:1.5px dashed #b4470c;color:#b4470c;border-radius:6px;padding:7px 5px">פתוחה</span>
      <span style="background:#e3f3eb;color:#1c6b4b;border-radius:6px;padding:8px 6px;font-weight:600">רועי</span>
      <span style="background:#e3f3eb;color:#1c6b4b;border-radius:6px;padding:8px 6px;font-weight:600">נועה</span>
      <span style="font-weight:600;align-self:center">חמ״ל</span>
      <span style="background:#f1e8fa;color:#6a2c91;border-radius:6px;padding:8px 6px;font-weight:600">מיכל</span>
      <span style="background:#f1e8fa;color:#6a2c91;border-radius:6px;padding:8px 6px;font-weight:600">תמר</span>
      <span style="background:#f1e8fa;color:#6a2c91;border-radius:6px;padding:8px 6px;font-weight:600">מיכל</span>
      <span style="background:#e8eefb;border:1.5px dashed #2b59c3;color:#1f4296;border-radius:6px;padding:7px 5px">שחרר כאן</span>
      <span style="background:#f1e8fa;color:#6a2c91;border-radius:6px;padding:8px 6px;font-weight:600">תמר</span>
    </div>
  </div>
  <div class="float-b" style="align-self:flex-start;background:#fff;color:#1a1a17;border-radius:12px;padding:10px 14px;display:flex;align-items:center;gap:10px;box-shadow:0 16px 40px rgba(0,0,0,.25);margin-right:40px">
    <span style="width:30px;height:30px;border-radius:50%;background:#f1e8fa;color:#6a2c91;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600">תג</span>
    <span style="font-size:13.5px;font-weight:500">תמר גולן</span>
    <span style="font-size:11.5px;color:#6a2c91;background:#f1e8fa;padding:1px 7px;border-radius:999px">סמבצית</span>
  </div>
</div>
<div style="display:flex;flex-direction:column;gap:10px;color:#fff;position:relative">
  <span style="font-family:Rubik,sans-serif;font-size:30px;font-weight:600;line-height:1.25">סידור עבודה הוגן,<br>בגרירה אחת.</span>
  <span style="font-size:16px;color:#c8d3ee;max-width:440px;line-height:1.55">המערכת בודקת שעות מנוחה, אילוצים אישיים ומכסות שבועיות בזמן שאתה משבץ, ומאזנת את העומס בין אנשי הצוות.</span>
</div>
"""


def log_in(user_id, username):
    app.storage.user.update({"user_id": user_id, "username": username})
    ui.navigate.to("/")


def strength(password):
    if not password:
        return 0, "var(--muted)", f"לפחות {MIN_PASSWORD_LENGTH} תווים"
    if len(password) < MIN_PASSWORD_LENGTH:
        return 30, "var(--warn)", "קצרה מדי"
    if len(password) >= 10 and any(c.isdigit() for c in password) and any(not c.isdigit() for c in password):
        return 100, "var(--ok)", "חזקה"
    return 65, "#8a6d00", "סבירה"


def build(mode="login"):
    apply_color_scheme()
    is_login = mode == "login"

    with ui.element("div").classes("auth-wrap"):
        with ui.element("section").classes("auth-form"):
            with ui.element("div").classes("flex items-center gap-3"):
                with ui.element("div").classes("rail-logo").style("margin: 0; width: 44px; height: 44px"):
                    icon("shield", 24, 2)
                ui.label("מערכת שיבוץ משמרות").classes("font-display text-xl font-bold")

            with ui.element("div").classes("flex flex-col gap-2"):
                ui.label("ברוך שובך" if is_login else "פתיחת חשבון").classes("page-title").props(
                    'role="heading" aria-level="1"'
                )
                ui.label(
                    "היכנס כדי לראות את סידור העבודה שלך."
                    if is_login
                    else "כל חשבון מקבל עולם נתונים משלו, עם 4 תפקידי ברירת מחדל."
                ).classes("muted")

            with ui.element("div").classes("segmented").style("display: grid; grid-template-columns: 1fr 1fr").props(
                'role="tablist" aria-label="כניסה או הרשמה"'
            ):
                for target, label, on in (("/login", "כניסה", is_login), ("/signup", "הרשמה", not is_login)):
                    tab = ui.element("button").classes("on" if on else "").style("justify-content: center").props(
                        f'type="button" role="tab" aria-selected="{str(on).lower()}"'
                    )
                    with tab:
                        ui.label(label)
                    tab.on("click", lambda t=target: ui.navigate.to(t))

            username = ui.input("שם משתמש").props('outlined autocomplete="username"').classes("w-full")
            password = ui.input("סיסמה", password=True, password_toggle_button=True).props(
                f'outlined autocomplete="{"current-password" if is_login else "new-password"}"'
            ).classes("w-full")

            if not is_login:
                @ui.refreshable
                def meter():
                    pct, color, text = strength(password.value or "")
                    with ui.element("div").classes("flex items-center gap-2 w-full").style("margin-top: -10px"):
                        with ui.element("div").classes("progress flex-grow").style("height: 5px"):
                            ui.element("div").style(f"width: {pct}%; background: {color}")
                        ui.label(text).classes("text-xs").style(f"color: {color}; min-width: 86px")

                meter()
                password.on_value_change(meter.refresh)
                confirm = ui.input("אימות סיסמה", password=True).props('outlined autocomplete="new-password"').classes("w-full")

            error = ui.label("").classes("text-sm warn-text").props('role="alert"').style(
                "background: var(--warn-soft); padding: 10px 12px; border-radius: 9px"
            )
            error.set_visibility(False)

            def show_error(text):
                error.set_text(text)
                error.set_visibility(True)

            async def submit():
                error.set_visibility(False)
                name = (username.value or "").strip()
                if is_login:
                    try:
                        user_id = await run.io_bound(authenticate, name, password.value)
                    except Exception as e:
                        show_error(f"שגיאת תקשורת עם מסד הנתונים: {e}")
                        return
                    if user_id is None:
                        show_error("שם משתמש או סיסמה שגויים")
                        return
                else:
                    if password.value != confirm.value:
                        show_error("הסיסמאות אינן תואמות")
                        return
                    try:
                        user_id = await run.io_bound(register, name, password.value)
                    except RegistrationError as e:
                        show_error(str(e))
                        return
                    except Exception as e:
                        show_error(f"שגיאת תקשורת עם מסד הנתונים: {e}")
                        return
                log_in(user_id, name)

            (password if is_login else confirm).on("keydown.enter", submit)
            button("כניסה" if is_login else "יצירת חשבון", on_click=submit).classes("w-full").mark("auth-submit").style("height: 50px")

        ui.html(ART, sanitize=False, tag="section").classes("auth-art").props('aria-hidden="true"')
