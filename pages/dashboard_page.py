from nicegui import run, ui

from db.connection import get_connection
from pages.ui_kit import (
    DAY_NAMES,
    button,
    db_error,
    fmt_time,
    icon,
    ltr,
    role_class,
    today,
    toast,
    week_label,
)
from pages.week_data import WeekData
from scheduler.allocator import generate_schedule

MAX_TODO = 5


def run_generate(user_id):
    conn = get_connection()
    try:
        return generate_schedule(conn, user_id)
    finally:
        conn.close()


def build(user_id):
    @ui.refreshable
    def content():
        try:
            data = WeekData(user_id, today())
        except Exception as e:
            db_error(e)
            return

        total = len(data.shifts)
        filled = data.filled_count
        open_shifts = data.open_shifts
        pct = round(filled / total * 100) if total else 0

        with ui.element("header").classes("header-row flex items-end justify-between gap-6"):
            with ui.element("div").classes("flex flex-col gap-1"):
                ui.label(week_label(data.week_start, data.week_end)).classes("muted text-sm")
                ui.label("סקירת השבוע").classes("page-title").props('role="heading" aria-level="1"')
            with ui.element("div").classes("flex gap-2 flex-wrap"):
                button("פתח לוח שיבוץ", kind="secondary", icon_name="calendar", href="/board")
                button("צור סידור עבודה", on_click=generate, icon_name="sparkle")

        if not data.personnel or not data.positions:
            empty_state(
                "בוא נתחיל",
                "כדי לשבץ צריך אנשי צוות ועמדות. הוסף אותם במסך הצוות.",
                "למסך הצוות",
                "/team",
            )
            return

        with ui.element("section").classes("stats-grid grid gap-4").style(
            "grid-template-columns: repeat(4, minmax(0, 1fr))"
        ).props('aria-label="מדדים"'):
            with ui.element("div").classes("card lift p-5 flex flex-col gap-2"):
                ui.label("משמרות השבוע").classes("muted text-sm")
                ui.label(str(total)).classes("stat-value")
                ui.label(f"{len(data.positions)} עמדות").classes("muted text-xs")
            with ui.element("div").classes("card lift p-5 flex flex-col gap-2"):
                ui.label("משובצות").classes("muted text-sm")
                with ui.element("div").classes("flex items-baseline gap-2"):
                    ui.label(str(filled)).classes("stat-value")
                    ui.label(f"{pct}%").classes("ok-text font-semibold")
                with ui.element("div").classes("progress"):
                    ui.element("div").style(f"width: {pct}%")
            with ui.element("a").classes("warn-card lift p-5 flex flex-col gap-2 no-underline").props('href="/board"').style(
                "color: var(--text)"
            ):
                with ui.element("div").classes("warn-text text-sm font-medium flex items-center gap-1"):
                    icon("alert", 16, 2)
                    ui.label("לא משובצות")
                ui.label(str(len(open_shifts))).classes("stat-value warn-text")
                ui.label("לחץ כדי לשבץ בלוח ←").classes("warn-text text-xs")
            with ui.element("div").classes("card lift p-5 flex flex-col gap-2"):
                ui.label("אנשי צוות").classes("muted text-sm")
                ui.label(str(len(data.personnel))).classes("stat-value")
                away = data.unavailable_on(today())
                if away:
                    names = ", ".join(u["Full_Name"] for u in away[:2])
                    note = f"{len(data.personnel) - len(away)} זמינים היום · {names} לא זמין"
                else:
                    note = "כולם זמינים היום"
                ui.label(note).classes("muted text-xs")

        if not data.shifts:
            empty_state(
                "אין עדיין משמרות לשבוע הזה",
                "צור משמרות לשבוע בלוח השיבוץ, ואז שבץ אוטומטית או בגרירה.",
                "ללוח השיבוץ",
                "/board",
            )
            return

        with ui.element("div").classes("two-col grid gap-4").style(
            "grid-template-columns: minmax(0, 1.25fr) minmax(0, 1fr)"
        ):
            balance_section(data)
            todo_section(data, open_shifts)

    async def generate():
        try:
            result = await run.io_bound(run_generate, user_id)
        except Exception as e:
            db_error(e)
            return
        assigned, unresolved = len(result["assigned"]), len(result["unresolved"])
        if assigned:
            toast(f"שובצו {assigned} משמרות" + (f" · {unresolved} לא ניתנות לשיבוץ" if unresolved else ""))
        elif unresolved:
            toast(f"{unresolved} משמרות לא ניתנות לשיבוץ – ראה 'דורש טיפול'", kind="warn")
        else:
            toast("כל המשמרות כבר משובצות")
        content.refresh()

    content()


def empty_state(title, text, cta, href):
    with ui.element("div").classes("card p-10 flex flex-col items-center gap-3 text-center"):
        ui.label(title).classes("section-title")
        ui.label(text).classes("muted")
        button(cta, href=href)


def balance_section(data):
    hours = data.week_hours()
    people = sorted(data.personnel, key=lambda p: hours[p["ID"]], reverse=True)
    top = max(list(hours.values()) + [1])
    avg = round(sum(hours.values()) / len(hours)) if hours else 0
    with ui.element("section").classes("card p-6 flex flex-col gap-3").props('aria-labelledby="balance-title"'):
        with ui.element("div").classes("flex justify-between items-baseline"):
            ui.label("איזון עומסים").classes("section-title").props('id="balance-title"')
            ui.label(f"שעות השבוע · ממוצע {avg} ש׳").classes("muted text-sm")
        for p in people:
            rc = role_class(p["Role"], data.role_names)
            h = hours[p["ID"]]
            with ui.element("div").classes(f"{rc} grid items-center gap-3").style(
                "grid-template-columns: 120px minmax(0, 1fr) 52px"
            ):
                with ui.element("div").classes("flex flex-col min-w-0"):
                    ui.label(p["Full_Name"]).classes("text-sm font-medium truncate")
                    ui.label(p["Role"]).classes("text-xs").style("color: var(--rc-fg)")
                with ui.element("div").classes("bar-track"):
                    ui.element("div").style(f"width: {round(h / top * 100)}%")
                ui.label(f"{h:g}h").classes("mono text-sm muted text-left")


def todo_section(data, open_shifts):
    with ui.element("section").classes("card p-6 flex flex-col gap-3").props('aria-labelledby="todo-title"'):
        with ui.element("div").classes("flex justify-between items-baseline"):
            ui.label("דורש טיפול").classes("section-title").props('id="todo-title"')
            ui.label(f"{len(open_shifts)} משמרות פתוחות").classes("muted text-sm")
        if not open_shifts:
            with ui.element("div").classes("flex flex-col items-center gap-2 py-8 ok-text"):
                icon("check_circle", 36)
                ui.label("הכל משובץ. שבוע שקט.").classes("font-semibold")
            return
        for s in open_shifts[:MAX_TODO]:
            reason = data.ctx.open_reason(s)
            fixable = reason.startswith("יש מי")
            day_name = DAY_NAMES[(s["Date"].weekday() + 1) % 7]
            with ui.element("a").classes("todo-row lift").props('href="/board"'):
                ui.element("span").classes("dot").style(f"background: var({'--muted' if fixable else '--warn'})")
                with ui.element("div").classes("flex flex-col flex-grow min-w-0"):
                    ui.label(f"יום {day_name} · {s['Position_Name']}").classes("text-sm font-medium")
                    ui.label(reason).classes("muted text-xs")
                ui.label(ltr(f"{fmt_time(s['Start_Time'])}–{fmt_time(s['End_Time'])}")).classes("mono text-xs muted")
        if len(open_shifts) > MAX_TODO:
            ui.link(f"ועוד {len(open_shifts) - MAX_TODO} בלוח השיבוץ ←", "/board").classes("text-sm font-medium").style(
                "color: var(--accent-text)"
            )
