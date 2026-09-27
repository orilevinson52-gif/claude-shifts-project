import mysql.connector
from nicegui import run, ui

from db.connection import (
    create_person,
    create_position,
    create_role,
    create_unavailability,
    delete_all_personnel,
    delete_all_positions,
    delete_all_roles,
    delete_all_unavailability,
    delete_person,
    delete_position,
    delete_role,
    delete_unavailability,
    get_connection,
    update_person,
    update_position,
    update_role,
)
from pages.ui_kit import button, db_error, fmt_date, icon, icon_button, initials, role_class, today, toast
from pages.week_data import WeekData

TABS = [
    ("people", "אנשי צוות", "הוסף איש צוות"),
    ("roles", "תפקידים", "הוסף תפקיד"),
    ("positions", "עמדות", "הוסף עמדה"),
    ("constraints", "אילוצים", "הוסף אילוץ"),
]
IN_USE_ERRORS = {
    "roles": "לא ניתן למחוק תפקיד שמשויך לאנשי צוות או לעמדות",
    "positions": "לא ניתן למחוק עמדה שיש לה משמרות",
}


def date_field(label, value=""):
    with ui.input(label, value=value).props("outlined").classes("w-full") as field:
        with field.add_slot("append"):
            picker_icon = ui.icon("edit_calendar").classes("cursor-pointer")
        with ui.menu() as menu:
            ui.date(mask="YYYY-MM-DD").bind_value(field)
        picker_icon.on("click", menu.open)
    return field


def build(user_id, tab="people"):
    state = {"tab": tab if tab in dict((t[0], t) for t in TABS) else "people", "q": ""}

    def db(fn, *args):
        conn = get_connection()
        try:
            return fn(conn, user_id, *args)
        finally:
            conn.close()

    async def mutate(fn, *args, success="נשמר", in_use=None):
        """Runs a write; returns True on success, shows a friendly error otherwise."""
        try:
            await run.io_bound(db, fn, *args)
        except mysql.connector.IntegrityError:
            toast(in_use or "כבר קיים פריט בשם הזה", kind="warn")
            return False
        except Exception as e:
            db_error(e)
            return False
        toast(success)
        content.refresh()
        return True

    def drawer(title):
        dialog = ui.dialog().props("position=left full-height")
        with dialog:
            card = ui.card().classes("sheet-card flex flex-col gap-4").style(
                "height: 100%; border-radius: 0 !important; width: 420px"
            )
            with card:
                with ui.element("div").classes("flex justify-between items-center w-full"):
                    ui.label(title).classes("section-title").style("font-size: 22px")
                    icon_button("x", "סגירה", dialog.close)
        return dialog, card

    def choice_buttons(options, selected, role_names):
        """Big tappable role buttons; returns a dict holding the selection."""
        chosen = {"value": selected}

        @ui.refreshable
        def render():
            with ui.element("div").classes("grid gap-2 w-full").style("grid-template-columns: repeat(2, minmax(0, 1fr))"):
                for name in options:
                    on = chosen["value"] == name
                    rc = role_class(name, role_names)
                    b = ui.element("button").classes(f"btn {rc}").props(f'type="button" aria-pressed="{str(on).lower()}"').style(
                        "background: var(--rc-bg); color: var(--rc-fg); border: 1.5px solid var(--rc-fg)"
                        if on else "background: transparent; color: var(--text); border: 1.5px solid var(--border)"
                    )
                    with b:
                        ui.label(name)
                    b.on("click", lambda n=name: (chosen.update(value=n), render.refresh()))

        render()
        return chosen

    # --- forms ---

    def person_form(data, row=None):
        roles = data.role_names
        if not roles:
            toast("יש להוסיף תפקיד לפני איש צוות", kind="warn")
            return
        dialog, card = drawer("עריכת איש צוות" if row else "איש צוות חדש")
        with card:
            name = ui.input("שם מלא", value=row["Full_Name"] if row else "").props("outlined").classes("w-full")
            ui.label("תפקיד").classes("text-sm font-medium")
            role = choice_buttons(roles, row["Role"] if row and row["Role"] in roles else roles[0], roles)
            ui.element("div").classes("flex-grow")

            async def save():
                if not (name.value or "").strip():
                    toast("יש להזין שם", kind="warn")
                    return
                if row:
                    ok = await mutate(update_person, row["ID"], name.value.strip(), role["value"])
                else:
                    ok = await mutate(create_person, name.value.strip(), role["value"], success="איש הצוות נוסף")
                if ok:
                    dialog.close()

            button("שמירה", on_click=save).classes("w-full").mark("drawer-save")
        dialog.open()

    def role_form(row=None):
        dialog, card = drawer("עריכת תפקיד" if row else "תפקיד חדש")
        with card:
            name = ui.input("שם תפקיד", value=row["Role_Name"] if row else "").props("outlined").classes("w-full")
            unlimited = ui.switch("ללא הגבלת משמרות בשבוע", value=not row or row["Max_Shifts_Per_Week"] is None)
            max_shifts = ui.number(
                "מקסימום משמרות בשבוע לאדם", min=1, format="%d",
                value=(row["Max_Shifts_Per_Week"] if row and row["Max_Shifts_Per_Week"] else 5),
            ).props("outlined").classes("w-full")
            max_shifts.bind_visibility_from(unlimited, "value", backward=lambda v: not v)
            ui.element("div").classes("flex-grow")

            async def save():
                if not (name.value or "").strip():
                    toast("יש להזין שם תפקיד", kind="warn")
                    return
                cap = None if unlimited.value else int(max_shifts.value or 1)
                if row:
                    ok = await mutate(update_role, row["Role_Name"], name.value.strip(), cap)
                else:
                    ok = await mutate(create_role, name.value.strip(), cap, success="התפקיד נוסף")
                if ok:
                    dialog.close()

            button("שמירה", on_click=save).classes("w-full").mark("drawer-save")
        dialog.open()

    def position_form(data, row=None):
        roles = data.role_names
        if not roles:
            toast("יש להוסיף תפקיד לפני עמדה", kind="warn")
            return
        dialog, card = drawer("עריכת עמדה" if row else "עמדה חדשה")
        with card:
            name = ui.input("שם עמדה", value=row["Position_Name"] if row else "").props("outlined").classes("w-full")
            ui.label("תפקיד נדרש").classes("text-sm font-medium")
            role = choice_buttons(roles, row["Required_Role"] if row and row["Required_Role"] in roles else roles[0], roles)
            ui.element("div").classes("flex-grow")

            async def save():
                if not (name.value or "").strip():
                    toast("יש להזין שם עמדה", kind="warn")
                    return
                if row:
                    ok = await mutate(update_position, row["Position_Name"], name.value.strip(), role["value"])
                else:
                    ok = await mutate(create_position, name.value.strip(), role["value"], success="העמדה נוספה")
                if ok:
                    dialog.close()

            button("שמירה", on_click=save).classes("w-full").mark("drawer-save")
        dialog.open()

    def constraint_form(data):
        if not data.personnel:
            toast("יש להוסיף איש צוות לפני אילוץ", kind="warn")
            return
        dialog, card = drawer("אילוץ חדש")
        with card:
            options = {p["ID"]: p["Full_Name"] for p in data.personnel}
            person = ui.select(options, label="איש צוות", value=data.personnel[0]["ID"]).props("outlined").classes("w-full")
            start = date_field("מתאריך")
            end = date_field("עד תאריך")
            reason = ui.input("סיבה (למשל מילואים, חופשה, טסט)").props("outlined").classes("w-full")
            ui.element("div").classes("flex-grow")

            async def save():
                if not start.value or not end.value:
                    toast("יש למלא תאריך התחלה וסיום", kind="warn")
                    return
                if end.value < start.value:
                    toast("תאריך הסיום חייב להיות אחרי תאריך ההתחלה", kind="warn")
                    return
                ok = await mutate(create_unavailability, person.value, start.value, end.value,
                                  (reason.value or "").strip() or None, success="האילוץ נוסף")
                if ok:
                    dialog.close()

            button("שמירה", on_click=save).classes("w-full").mark("drawer-save")
        dialog.open()

    def confirm(text, action):
        with ui.dialog() as dialog, ui.card().classes("sheet-card flex flex-col gap-4"):
            ui.label(text).classes("section-title")

            async def go():
                dialog.close()
                await action()

            with ui.element("div").classes("flex gap-2 justify-end w-full"):
                button("ביטול", kind="secondary", on_click=dialog.close)
                button("מחק", kind="danger", on_click=go)
        dialog.open()

    # --- rendering ---

    @ui.refreshable
    def content():
        try:
            data = WeekData(user_id, today())
        except Exception as e:
            db_error(e)
            return
        current = state["tab"]
        add_label = dict((t[0], t[2]) for t in TABS)[current]
        counts = {"people": len(data.personnel), "roles": len(data.roles), "positions": len(data.positions),
                  "constraints": len(data.unavailability)}
        add_actions = {
            "people": lambda: person_form(data),
            "roles": lambda: role_form(),
            "positions": lambda: position_form(data),
            "constraints": lambda: constraint_form(data),
        }

        with ui.element("header").classes("header-row flex items-end justify-between gap-6"):
            with ui.element("div").classes("flex flex-col gap-1"):
                ui.label("כל מה שהשיבוץ נשען עליו").classes("muted text-sm")
                ui.label("צוות").classes("page-title").props('role="heading" aria-level="1"')
            button(add_label, icon_name="plus", on_click=add_actions[current]).mark("add-button")

        with ui.element("div").classes("flex items-center justify-between gap-4 flex-wrap"):
            with ui.element("div").classes("segmented").props('role="tablist" aria-label="סוג נתונים"').style(
                "overflow-x: auto; max-width: 100%"
            ):
                for key, label, _ in TABS:
                    b = ui.element("button").classes("on" if key == current else "").props(
                        f'type="button" role="tab" aria-selected="{str(key == current).lower()}"'
                    )
                    with b:
                        ui.label(label)
                        ui.label(str(counts[key])).classes("mono text-xs muted")
                    b.on("click", lambda k=key: (state.update(tab=k), content.refresh()))
            if current == "people":
                search = ui.input(placeholder="חיפוש לפי שם או תפקיד…", value=state["q"]).props(
                    'outlined dense clearable aria-label="חיפוש איש צוות"'
                ).style("width: 300px; max-width: 100%")
                search.on_value_change(lambda e: (state.update(q=e.value or ""), people_grid.refresh()))

        if current == "people":
            people_grid(data)
        elif current == "roles":
            roles_grid(data)
        elif current == "positions":
            positions_grid(data)
        else:
            constraints_list(data)

        clear_fns = {"people": delete_all_personnel, "roles": delete_all_roles, "positions": delete_all_positions,
                     "constraints": delete_all_unavailability}
        if counts[current]:
            label = dict((t[0], t[1]) for t in TABS)[current]
            button(f"מחק את כל ה{label}", kind="ghost", icon_name="trash",
                   on_click=lambda: confirm(
                       f"למחוק את כל ה{label}? הפעולה בלתי הפיכה.",
                       lambda: mutate(clear_fns[current], success="נמחק", in_use=IN_USE_ERRORS.get(current)),
                   )).classes("self-start")

    @ui.refreshable
    def people_grid(data):
        q = state["q"].strip()
        hours = data.week_hours()
        shown = [p for p in data.personnel if not q or q in p["Full_Name"] or q in p["Role"]]
        if not data.personnel:
            empty("עדיין אין אנשי צוות", "הוסף את הראשון כדי להתחיל לשבץ.")
            return
        if not shown:
            ui.label("לא נמצאו אנשי צוות שמתאימים לחיפוש.").classes("muted p-8 text-center w-full")
            return
        top = max(list(hours.values()) + [40])
        with ui.element("div").classes("cards-grid grid gap-4").style("grid-template-columns: repeat(4, minmax(0, 1fr))"):
            for p in shown:
                rc = role_class(p["Role"], data.role_names)
                away = [u for u in data.unavailability if u["Person_ID"] == p["ID"] and u["End_Date"] >= today()]
                with ui.element("article").classes(f"card lift p-4 flex flex-col gap-3 {rc}"):
                    with ui.element("div").classes("flex items-center gap-3"):
                        ui.label(initials(p["Full_Name"])).classes("avatar").style("width: 44px; height: 44px")
                        with ui.element("div").classes("flex flex-col gap-1 flex-grow min-w-0"):
                            ui.label(p["Full_Name"]).classes("font-semibold truncate")
                            ui.label(p["Role"]).classes("pill self-start")
                        icon_button("edit", f"עריכת {p['Full_Name']}", lambda row=p: person_form(data, row), 16)
                        icon_button("trash", f"מחיקת {p['Full_Name']}", lambda row=p: confirm(
                            f'למחוק את "{row["Full_Name"]}"?',
                            lambda: mutate(delete_person, row["ID"], success="נמחק"),
                        ), 16)
                    with ui.element("div").classes("flex flex-col gap-1"):
                        with ui.element("div").classes("flex justify-between text-xs muted"):
                            ui.label("שעות השבוע")
                            ui.label(f"{hours[p['ID']]:g}h").classes("mono").style("color: var(--text)")
                        with ui.element("div").classes("bar-track").style("height: 6px"):
                            ui.element("div").style(f"width: {round(hours[p['ID']] / top * 100)}%")
                    if away:
                        u = away[0]
                        when = fmt_date(u["Start_Date"]) + ("" if u["Start_Date"] == u["End_Date"] else f"–{fmt_date(u['End_Date'])}")
                        status, color = f"לא זמין {when}" + (f" · {u['Reason']}" if u["Reason"] else ""), "var(--warn)"
                    else:
                        status, color = "אין אילוצים קרובים", "var(--ok)"
                    with ui.element("div").classes("flex items-center gap-2 text-xs").style(f"color: {color}"):
                        ui.element("span").classes("dot").style(f"background: {color}; width: 7px; height: 7px")
                        ui.label(status)

    def roles_grid(data):
        if not data.roles:
            empty("עדיין אין תפקידים", "תפקיד קובע מי יכול לאייש איזו עמדה, ואפשר להגביל כמה משמרות בשבוע.")
            return
        with ui.element("div").classes("cards-grid grid gap-4").style("grid-template-columns: repeat(4, minmax(0, 1fr))"):
            for r in data.roles:
                rc = role_class(r["Role_Name"], data.role_names)
                people = sum(1 for p in data.personnel if p["Role"] == r["Role_Name"])
                positions = sum(1 for p in data.positions if p["Required_Role"] == r["Role_Name"])
                with ui.element("article").classes(f"card lift p-5 flex flex-col gap-2 {rc}").style(
                    "border-top: 4px solid var(--rc-bar)"
                ):
                    with ui.element("div").classes("flex justify-between items-center"):
                        ui.label(r["Role_Name"]).classes("font-display text-xl font-semibold")
                        with ui.element("div").classes("flex"):
                            icon_button("edit", f"עריכת {r['Role_Name']}", lambda row=r: role_form(row), 16)
                            icon_button("trash", f"מחיקת {r['Role_Name']}", lambda row=r: confirm(
                                f'למחוק את התפקיד "{row["Role_Name"]}"?',
                                lambda: mutate(delete_role, row["Role_Name"], success="נמחק", in_use=IN_USE_ERRORS["roles"]),
                            ), 16)
                    cap = r["Max_Shifts_Per_Week"]
                    ui.label(f"עד {cap} משמרות בשבוע לאדם" if cap else "ללא הגבלת משמרות").classes("muted text-sm")
                    ui.label(f"{people} אנשי צוות · {positions} עמדות").classes("text-sm")

    def positions_grid(data):
        if not data.positions:
            empty("עדיין אין עמדות", "עמדה היא מקום שצריך לאייש, עם התפקיד שנדרש בה.")
            return
        with ui.element("div").classes("cards-grid grid gap-4").style("grid-template-columns: repeat(4, minmax(0, 1fr))"):
            for p in data.positions:
                rc = role_class(p["Required_Role"], data.role_names)
                week_count = sum(1 for s in data.shifts if s["Position_Name"] == p["Position_Name"])
                with ui.element("article").classes(f"card lift p-5 flex flex-col gap-2 {rc}"):
                    with ui.element("div").classes("flex justify-between items-center"):
                        ui.label(p["Position_Name"]).classes("font-display text-xl font-semibold")
                        with ui.element("div").classes("flex"):
                            icon_button("edit", f"עריכת {p['Position_Name']}", lambda row=p: position_form(data, row), 16)
                            icon_button("trash", f"מחיקת {p['Position_Name']}", lambda row=p: confirm(
                                f'למחוק את העמדה "{row["Position_Name"]}"?',
                                lambda: mutate(delete_position, row["Position_Name"], success="נמחק",
                                               in_use=IN_USE_ERRORS["positions"]),
                            ), 16)
                    ui.label(f"נדרש: {p['Required_Role']}").classes("pill self-start")
                    ui.label(f"{week_count} משמרות השבוע").classes("muted text-sm")

    def constraints_list(data):
        if not data.unavailability:
            empty("אין אילוצים", "אילוץ הוא תאריכים שבהם איש צוות לא זמין – חופשה, מילואים, טסט.")
            return
        with ui.element("div").classes("card flex flex-col"):
            for u in data.unavailability:
                with ui.element("div").classes("flex items-center gap-4 flex-wrap px-5 py-4").style(
                    "border-bottom: 1px solid var(--border)"
                ):
                    ui.label(u["Full_Name"]).classes("font-semibold").style("min-width: 180px")
                    dates = u["Start_Date"].strftime("%d.%m.%Y") + (
                        "" if u["Start_Date"] == u["End_Date"] else " – " + u["End_Date"].strftime("%d.%m.%Y")
                    )
                    ui.label(dates).classes("mono text-sm muted").style("min-width: 200px")
                    ui.label(u["Reason"] or "").classes("flex-grow text-sm")
                    icon_button("trash", "מחיקת אילוץ", lambda row=u: confirm(
                        f'למחוק את האילוץ של "{row["Full_Name"]}"?',
                        lambda: mutate(delete_unavailability, row["ID"], success="נמחק"),
                    ), 16)

    def empty(title, text):
        with ui.element("div").classes("card p-10 flex flex-col items-center gap-2 text-center"):
            icon("users", 32)
            ui.label(title).classes("section-title")
            ui.label(text).classes("muted")

    content()
