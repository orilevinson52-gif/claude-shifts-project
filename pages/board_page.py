from datetime import date, timedelta

from nicegui import run, ui

from db.connection import clear_assignments_between, delete_shift, get_connection, set_shift_assignment
from pages import week_builder
from pages.dashboard_page import run_generate
from pages.ui_kit import (
    DAY_LETTERS,
    DAY_NAMES,
    button,
    db_error,
    fmt_date,
    fmt_time,
    icon,
    icon_button,
    initials,
    ltr,
    role_class,
    today,
    toast,
    week_label,
)
from pages.week_data import WeekData

DRAG_START_JS = "(e) => { e.dataTransfer.setData('text/plain', ''); e.dataTransfer.effectAllowed = 'move'; emit(); }"
ALLOW_DROP_JS = "(e) => e.preventDefault()"
DROP_JS = "(e) => { e.preventDefault(); emit(); }"


def day_index(day):
    """0 = Sunday."""
    return (day.weekday() + 1) % 7


def time_range(shift):
    return ltr(f"{fmt_time(shift['Start_Time'])}–{fmt_time(shift['End_Time'])}")


def set_title(element, text):
    element._props["title"] = text
    element.update()


def parse_week(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return today()


async def build(user_id, week_param=None):
    anchor = parse_week(week_param)
    state = {"drag": None, "just": None, "q": "", "day": None}
    cards = {}  # shift id -> {"el", "label", "shift", "base"}
    chips = {}  # person id -> element
    holder = {}

    def with_conn(fn, *args):
        conn = get_connection()
        try:
            return fn(conn, user_id, *args)
        finally:
            conn.close()

    # --- drag & drop ---

    def start_drag(person_id):
        data = holder["data"]
        person = data.ctx.people_by_id.get(person_id)
        if person is None:
            return
        state["drag"] = person_id
        ok_count = 0
        for sid, card in cards.items():
            shift = card["shift"]
            if shift["Assigned_Person_ID"] == person_id:
                mode, reason = "is-self", None
            else:
                reason = data.ctx.reason(shift, person)
                mode = "is-blocked" if reason else "is-ok"
            if mode == "is-ok":
                ok_count += 1
            card["el"].classes(replace=f"{card['base']} {mode}")
            set_title(card["el"], f"לא ניתן: {reason}" if reason else card["title"])
            if card["label"] is not None and shift["Assigned_Person_ID"] is None:
                card["label"].set_text("שחרר כאן" if mode == "is-ok" else "פתוחה")
        for pid, chip in chips.items():
            chip.classes(add="dragging") if pid == person_id else chip.classes(remove="dragging")
        banner_text.set_text(f"משבצים את {person['Full_Name']} · {ok_count} משמרות מתאימות מסומנות")
        banner.set_visibility(True)

    def end_drag():
        if state["drag"] is None:
            return
        state["drag"] = None
        for card in cards.values():
            card["el"].classes(replace=card["base"])
            set_title(card["el"], card["title"])
            if card["label"] is not None and card["shift"]["Assigned_Person_ID"] is None:
                card["label"].set_text("פתוחה")
        for chip in chips.values():
            chip.classes(remove="dragging")
        banner.set_visibility(False)

    async def drop(shift_id):
        person_id = state["drag"]
        end_drag()
        if person_id is None:
            return
        await assign(shift_id, person_id)

    async def assign(shift_id, person_id):
        data = holder["data"]
        shift = next((s for s in data.shifts if s["Shift_ID"] == shift_id), None)
        person = data.ctx.people_by_id.get(person_id) if person_id else None
        if shift is None:
            return
        if person is not None:
            if shift["Assigned_Person_ID"] == person_id:
                return
            reason = data.ctx.reason(shift, person)
            if reason:
                toast(f"אי אפשר לשבץ את {person['Full_Name']}: {reason}", kind="warn")
                return
        try:
            await run.io_bound(with_conn, set_shift_assignment, shift_id, person_id)
        except Exception as e:
            db_error(e)
            return
        if person is not None:
            state["just"] = shift_id
        await reload()
        if person is not None:
            day_name = DAY_NAMES[day_index(shift["Date"])]
            toast(f"{person['Full_Name']} שובץ ל{shift['Position_Name']} · {day_name} {time_range(shift)}")
        else:
            toast("השיבוץ הוסר")

    # --- dialogs ---

    def open_shift_dialog(shift):
        data = holder["data"]
        day_name = DAY_NAMES[day_index(shift["Date"])]
        with ui.dialog().props("position=bottom" if state.get("mobile") else "") as dialog, ui.card().classes(
            "sheet-card flex flex-col gap-3"
        ):
            with ui.element("div").classes("flex justify-between items-start w-full"):
                with ui.element("div").classes("flex flex-col"):
                    ui.label(f"{shift['Position_Name']} · {time_range(shift)}").classes("section-title")
                    ui.label(
                        f"יום {day_name} {fmt_date(shift['Date'])} · מוצגים רק מי שבתפקיד {shift['Required_Role']}"
                    ).classes("muted text-sm")
                icon_button("x", "סגירה", dialog.close)
            candidates = data.ctx.candidates(shift)
            if not candidates:
                ui.label(f"אין אנשי צוות בתפקיד {shift['Required_Role']}. הוסף במסך הצוות.").classes("muted")
            with ui.element("div").classes("flex flex-col gap-2 w-full").style("max-height: 50vh; overflow: auto"):
                for person, reason in candidates:
                    current = person["ID"] == shift["Assigned_Person_ID"]
                    rc = role_class(person["Role"], data.role_names)
                    classes = "candidate" + (" current" if current else "") + (" blocked" if reason else "")
                    row = ui.element("button").classes(f"{classes} {rc}").props('type="button"').mark(f"candidate-{person['ID']}")
                    if reason:
                        row.props("disabled")
                    with row:
                        ui.label(initials(person["Full_Name"])).classes("avatar text-sm").style("width: 36px; height: 36px")
                        with ui.element("div").classes("flex flex-col flex-grow items-start"):
                            ui.label(person["Full_Name"]).classes("font-semibold")
                            note = "משובץ כרגע" if current else (reason or "פנוי · מסודר לפי שעות")
                            ui.label(note).classes("text-xs " + ("warn-text" if reason else "ok-text"))
                        ui.label(f"{float(person['Total_Hours_Done']):g}h").classes("mono text-xs muted")
                    if not reason and not current:
                        row.on("click", lambda pid=person["ID"]: (dialog.close(), assign(shift["Shift_ID"], pid))[1])
            with ui.element("div").classes("flex gap-2 w-full justify-between flex-wrap"):
                if shift["Assigned_Person_ID"] is not None:
                    button("הסר שיבוץ", kind="danger",
                           on_click=lambda: (dialog.close(), assign(shift["Shift_ID"], None))[1])
                button("מחק משמרת", kind="ghost", icon_name="trash",
                       on_click=lambda: (dialog.close(), confirm_delete_shift(shift)))
        dialog.open()

    def confirm_delete_shift(shift):
        with ui.dialog() as dialog, ui.card().classes("sheet-card flex flex-col gap-4"):
            ui.label(f"למחוק את המשמרת {shift['Position_Name']} {time_range(shift)}?").classes("section-title")
            ui.label("אם מישהו משובץ אליה, השעות יורדו לו.").classes("muted text-sm")

            async def do_delete():
                dialog.close()
                try:
                    if shift["Assigned_Person_ID"] is not None:
                        await run.io_bound(with_conn, set_shift_assignment, shift["Shift_ID"], None)
                    await run.io_bound(with_conn, delete_shift, shift["Shift_ID"])
                except Exception as e:
                    db_error(e)
                    return
                toast("המשמרת נמחקה")
                await reload()

            with ui.element("div").classes("flex gap-2 justify-end w-full"):
                button("ביטול", kind="secondary", on_click=dialog.close)
                button("מחק", kind="danger", on_click=do_delete)
        dialog.open()

    def confirm_clear_week():
        data = holder["data"]
        with ui.dialog() as dialog, ui.card().classes("sheet-card flex flex-col gap-4"):
            ui.label("לנקות את כל השיבוצים של השבוע?").classes("section-title")
            ui.label("המשמרות נשארות, רק השיבוצים מתבטלים והשעות יורדות.").classes("muted text-sm")

            async def do_clear():
                dialog.close()
                try:
                    await run.io_bound(with_conn, clear_assignments_between, data.week_start, data.week_end)
                except Exception as e:
                    db_error(e)
                    return
                toast("השבוע נוקה")
                await reload()

            with ui.element("div").classes("flex gap-2 justify-end w-full"):
                button("ביטול", kind="secondary", on_click=dialog.close)
                button("נקה", kind="danger", on_click=do_clear)
        dialog.open()

    async def auto_schedule():
        try:
            result = await run.io_bound(run_generate, user_id)
        except Exception as e:
            db_error(e)
            return
        assigned, unresolved = len(result["assigned"]), len(result["unresolved"])
        if assigned:
            toast(f"שובצו {assigned} משמרות" + (f" · {unresolved} לא ניתנות לשיבוץ" if unresolved else ""))
        elif unresolved:
            toast(f"{unresolved} משמרות לא ניתנות לשיבוץ – עבור עם העכבר כדי לראות למה", kind="warn")
        else:
            toast("כל המשמרות כבר משובצות")
        await reload()

    # --- rendering ---

    async def reload():
        """Loads fresh data off the event loop, then swaps the screen in one step (no blank flash)."""
        try:
            data = await run.io_bound(WeekData, user_id, anchor)
        except Exception as e:
            db_error(e)
            return
        holder["data"] = data
        content.refresh(data)

    @ui.refreshable
    def content(data=None):
        if data is None:
            return
        cards.clear()
        chips.clear()
        prev_week = (data.week_start - timedelta(days=7)).isoformat()
        next_week = (data.week_start + timedelta(days=7)).isoformat()
        total, filled = len(data.shifts), data.filled_count
        pct = round(filled / total * 100) if total else 0

        with ui.element("header").classes("header-row flex items-center justify-between gap-4 flex-wrap"):
            with ui.element("div").classes("flex items-center gap-4 flex-wrap"):
                ui.label("לוח שיבוץ").classes("page-title").props('role="heading" aria-level="1"')
                with ui.element("div").classes("card flex items-center").style("padding: 3px; border-radius: 10px").props(
                    'data-tour="week-nav"'
                ):
                    with ui.element("a").classes("icon-btn").props(f'href="/board?week={prev_week}" aria-label="שבוע קודם"'):
                        icon("chev_right", 18, 2)
                    ui.label(week_label(data.week_start, data.week_end)).classes("text-sm font-medium px-2").style(
                        "min-width: 190px; text-align: center"
                    )
                    with ui.element("a").classes("icon-btn").props(f'href="/board?week={next_week}" aria-label="שבוע הבא"'):
                        icon("chev_left", 18, 2)
                if total:
                    with ui.element("div").classes("flex items-center gap-2 text-sm muted"):
                        with ui.element("div").classes("progress").style("width: 120px"):
                            ui.element("div").style(f"width: {pct}%")
                        ui.html(f"<b style='color: var(--text)'>{filled}</b> / {total} משובצות", sanitize=False)
            with ui.element("div").classes("flex gap-2 flex-wrap"):
                button("משמרות לשבוע", kind="secondary", icon_name="list_plus",
                       on_click=lambda: week_builder.open_dialog(user_id, data.week_start, data.positions, reload)
                       ).props('data-tour="week-builder"')
                if total:
                    button("נקה שבוע", kind="secondary", on_click=confirm_clear_week)
                    button("שבץ אוטומטית", icon_name="sparkle", on_click=auto_schedule).mark("auto-schedule").props(
                        'data-tour="auto-schedule"'
                    )

        if not data.positions or not data.personnel:
            with ui.element("div").classes("card p-10 flex flex-col items-center gap-3 text-center").props(
                'data-tour="board-empty"'
            ):
                ui.label("חסרים אנשי צוות או עמדות").classes("section-title")
                ui.label("הוסף אותם במסך הצוות, ואז חזור לכאן לבנות את השבוע.").classes("muted")
                button("למסך הצוות", href="/team")
            return
        if not data.shifts:
            with ui.element("div").classes("card p-10 flex flex-col items-center gap-3 text-center").props(
                'data-tour="board-empty"'
            ):
                ui.label("אין משמרות בשבוע הזה").classes("section-title")
                ui.label("הגדר אילו משמרות יש בכל עמדה בכל יום, ואז שבץ בגרירה או אוטומטית.").classes("muted")
                button("צור משמרות לשבוע", icon_name="list_plus",
                       on_click=lambda: week_builder.open_dialog(user_id, data.week_start, data.positions, reload))
            return

        desktop_board(data)
        mobile_board(data)
        state["just"] = None

    def desktop_board(data):
        with ui.element("div").classes("lg-only flex no-wrap gap-4 items-start"):
            with ui.element("aside").classes("card p-4 flex flex-col gap-3").style(
                "width: clamp(190px, 17vw, 236px); flex-shrink: 0; position: sticky; top: 16px; max-height: calc(100vh - 140px); overflow-y: auto"
            ).classes("people-panel").props('aria-label="אנשי צוות" data-tour="people-panel"'):
                with ui.element("div").classes("flex flex-col"):
                    ui.label("אנשי צוות").classes("font-display font-semibold")
                    ui.label("גרור אל משמרת כדי לשבץ").classes("muted text-xs")
                search = ui.input(placeholder="חיפוש…", value=state["q"]).props(
                    'dense outlined clearable aria-label="חיפוש איש צוות"'
                ).classes("w-full")
                people_list(data)
                search.on_value_change(lambda e: (state.update(q=e.value or ""), people_list.refresh()))

            with ui.element("section").classes("card p-3 flex flex-col gap-2 flex-grow min-w-0").props(
                'aria-label="לוח שבועי"'
            ):
                global_banner()
                with ui.element("div").classes("board-grid"):
                    ui.element("span")
                    for day in data.days:
                        head = ui.element("div").classes("day-head" + (" today" if day == today() else ""))
                        with head:
                            ui.label(DAY_NAMES[day_index(day)]).classes("text-sm font-semibold")
                            ui.label(fmt_date(day)).classes("mono text-xs muted")
                for position in data.positions:
                    rc = role_class(position["Required_Role"], data.role_names)
                    with ui.element("div").classes("board-grid"):
                        with ui.element("div").classes(f"{rc} flex flex-col justify-center gap-1 px-1"):
                            ui.label(position["Position_Name"]).classes("text-sm font-semibold")
                            ui.label(position["Required_Role"]).classes("pill self-start")
                        for day in data.days:
                            with ui.element("div").classes("flex flex-col gap-1"):
                                for shift in data.shifts:
                                    if shift["Date"] == day and shift["Position_Name"] == position["Position_Name"]:
                                        shift_card(data, shift)
                with ui.element("div").classes("flex gap-4 flex-wrap text-xs muted px-1 pt-1"):
                    ui.html(
                        "<span style='display:inline-flex;align-items:center;gap:6px'><span style='width:12px;height:12px;"
                        "border-radius:3px;border:1.5px dashed var(--accent);background:var(--accent-soft)'></span>אפשר לשבץ</span>",
                        sanitize=False,
                    )
                    ui.html(
                        "<span style='display:inline-flex;align-items:center;gap:6px'><span style='width:12px;height:12px;"
                        "border-radius:3px;border:1.5px dashed var(--warn)'></span>משמרת פתוחה</span>",
                        sanitize=False,
                    )
                    ui.label("לחיצה על משמרת פותחת רשימת מועמדים · מעבר עם העכבר על משבצת חסומה מסביר למה")

    def global_banner():
        nonlocal banner, banner_text
        banner = ui.element("div").classes("drag-banner")
        with banner:
            icon("arrow", 16, 2)
            banner_text = ui.label("")
        banner.set_visibility(False)

    @ui.refreshable
    def people_list(data=None):
        data = data or holder["data"]
        hours = data.week_hours()
        q = state["q"].strip()
        with ui.element("div").classes("flex flex-col gap-2").style("overflow: auto"):
            shown = [p for p in data.personnel if not q or q in p["Full_Name"] or q in p["Role"]]
            if not shown:
                ui.label("לא נמצאו אנשי צוות").classes("muted text-sm")
            for p in shown:
                rc = role_class(p["Role"], data.role_names)
                chip = ui.element("div").classes(f"chip {rc}").props(
                    f'draggable="true" aria-label="גרור את {p["Full_Name"]} אל משמרת"'
                )
                chip.mark(f"chip-{p['ID']}")
                chips[p["ID"]] = chip
                with chip:
                    ui.label(initials(p["Full_Name"])).classes("avatar text-xs").style("width: 32px; height: 32px")
                    with ui.element("div").classes("flex flex-col gap-1 flex-grow min-w-0"):
                        with ui.element("div").classes("flex justify-between gap-1"):
                            ui.label(p["Full_Name"]).classes("text-sm font-medium truncate")
                            ui.label(f"{hours[p['ID']]:g}h").classes("mono text-xs muted")
                        ui.label(p["Role"]).classes("pill self-start").style("font-size: 11.5px")
                chip.on("dragstart", lambda pid=p["ID"]: start_drag(pid), js_handler=DRAG_START_JS)
                chip.on("dragend", end_drag)

    def shift_card(data, shift):
        person_id = shift["Assigned_Person_ID"]
        is_open = person_id is None
        base = "shift-card " + ("is-open" if is_open else role_class(shift["Assigned_Role"], data.role_names))
        if state["just"] == shift["Shift_ID"]:
            base += " pop"
        day_name = DAY_NAMES[day_index(shift["Date"])]
        title = (
            f"{shift['Position_Name']} · {day_name} {fmt_time(shift['Start_Time'])}–{fmt_time(shift['End_Time'])}"
            + (" · פתוחה" if is_open else f" · {shift['Assigned_Name']}")
        )
        el = ui.element("div").classes(base).props('role="button" tabindex="0" data-tour="shift-card"').mark(f"shift-{shift['Shift_ID']}")
        el._props["title"] = title
        el._props["aria-label"] = title
        with el:
            ui.label(time_range(shift)).classes("mono shift-time")
            label = ui.label("פתוחה" if is_open else shift["Assigned_Name"]).classes("shift-name")
        cards[shift["Shift_ID"]] = {"el": el, "label": label, "shift": shift, "base": base, "title": title}
        el.on("dragover", js_handler=ALLOW_DROP_JS)
        el.on("dragenter", js_handler=ALLOW_DROP_JS)
        el.on("drop", lambda sid=shift["Shift_ID"]: drop(sid), js_handler=DROP_JS)
        el.on("click", lambda s=shift: open_shift_dialog(s))
        el.on("keydown.enter", lambda s=shift: open_shift_dialog(s))

    def mobile_board(data):
        days = data.days
        if state["day"] is None:
            state["day"] = days.index(today()) if today() in days else 0

        @ui.refreshable
        def day_view():
            day = days[state["day"]]
            with ui.element("div").classes("grid gap-1 w-full").style("grid-template-columns: repeat(7, minmax(0, 1fr))").props(
                'role="tablist" aria-label="ימי השבוע" data-tour="day-pills"'
            ):
                for i, d in enumerate(days):
                    has_open = any(s["Date"] == d and s["Assigned_Person_ID"] is None for s in data.shifts)
                    pill_btn = ui.element("button").classes("day-pill" + (" on" if i == state["day"] else "")).props(
                        f'type="button" role="tab" aria-selected="{str(i == state["day"]).lower()}" '
                        f'aria-label="יום {DAY_NAMES[day_index(d)]} {fmt_date(d)}"'
                    )
                    with pill_btn:
                        ui.label(DAY_LETTERS[day_index(d)]).classes("text-sm font-semibold")
                        ui.label(fmt_date(d)).classes("mono").style("font-size: 11px")
                        if has_open:
                            ui.element("span").classes("dot").style(
                                "position: absolute; top: 5px; left: 6px; width: 6px; height: 6px; background: var(--warn)"
                            )
                    pill_btn.on("click", lambda idx=i: (state.update(day=idx), day_view.refresh()))
            for position in data.positions:
                day_shifts = [s for s in data.shifts if s["Date"] == day and s["Position_Name"] == position["Position_Name"]]
                if not day_shifts:
                    continue
                rc = role_class(position["Required_Role"], data.role_names)
                with ui.element("section").classes("flex flex-col gap-2 w-full"):
                    with ui.element("div").classes(f"{rc} flex items-center gap-2"):
                        ui.label(position["Position_Name"]).classes("font-semibold")
                        ui.label(position["Required_Role"]).classes("pill")
                    for s in day_shifts:
                        is_open = s["Assigned_Person_ID"] is None
                        row = ui.element("button").classes(
                            "m-shift " + ("is-open" if is_open else role_class(s["Assigned_Role"], data.role_names))
                        ).props('type="button" data-tour="m-shift"')
                        with row:
                            ui.label(time_range(s)).classes("mono text-xs muted").style("white-space: nowrap")
                            ui.label("פתוחה – הקש לשיבוץ" if is_open else s["Assigned_Name"]).classes(
                                "flex-grow font-semibold text-right"
                            )
                            icon("chev_left", 18, 2)
                        row.on("click", lambda shift=s: (state.update(mobile=True), open_shift_dialog(shift)))

        with ui.element("div").classes("sm-only flex-col gap-4 w-full"):
            day_view()

    banner = None
    banner_text = None
    content()
    await reload()
