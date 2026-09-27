from datetime import datetime, timedelta

from nicegui import run, ui

from db.connection import create_shift, get_all_shifts, get_connection
from pages.ui_kit import DAY_NAMES, button, db_error, fmt_date, icon_button, ltr, toast

HOUR_OPTIONS = [f"{h:02d}:00" for h in range(24)]
PRESETS = [("06:00", "14:00"), ("14:00", "22:00"), ("22:00", "06:00")]


def create_week_shifts(user_id, week_start, template):
    """Creates the template's shifts for the week, skipping ones that already exist. Returns the count."""
    conn = get_connection()
    try:
        existing = {
            (row["Date"], row["Position_Name"], row["Start_Time"].strftime("%H:%M"))
            for row in get_all_shifts(conn, user_id)
        }
        created = 0
        for position, days in template.items():
            for day_idx, ranges in days.items():
                shift_date = week_start + timedelta(days=day_idx)
                for start_val, end_val in ranges:
                    if (shift_date, position, start_val) in existing:
                        continue
                    start_dt = datetime.combine(shift_date, datetime.strptime(start_val, "%H:%M").time())
                    end_dt = datetime.combine(shift_date, datetime.strptime(end_val, "%H:%M").time())
                    if end_dt <= start_dt:
                        end_dt += timedelta(days=1)
                    create_shift(conn, user_id, shift_date, start_dt, end_dt, position)
                    created += 1
        return created
    finally:
        conn.close()


def open_dialog(user_id, week_start, positions, on_done):
    template = {p["Position_Name"]: {i: [] for i in range(7)} for p in positions}

    with ui.dialog().props("maximized") as dialog, ui.card().classes("w-full h-full").style(
        "background: var(--bg) !important; color: var(--text); padding: 28px"
    ):
        with ui.element("div").classes("flex justify-between items-start w-full gap-4"):
            with ui.element("div").classes("flex flex-col gap-1"):
                ui.label("משמרות לשבוע").classes("page-title")
                ui.label(
                    f"{fmt_date(week_start)} – {fmt_date(week_start + timedelta(days=6))} · "
                    "הוסף טווחי שעות לכל עמדה בכל יום. משמרות שכבר קיימות לא ייווצרו פעמיים."
                ).classes("muted")
            icon_button("x", "סגירה", dialog.close, 20)

        with ui.element("div").classes("flex items-center gap-2 flex-wrap"):
            ui.label("מילוי מהיר לכל העמדות וכל הימים:").classes("text-sm muted")
            for start, end in PRESETS:
                button(ltr(f"{start}–{end}"), kind="secondary",
                       on_click=lambda s=start, e=end: fill_all(s, e)).style("height: 36px; font-size: 13.5px")

        @ui.refreshable
        def grid():
            with ui.element("div").classes("w-full").style("overflow-x: auto"):
                with ui.element("div").classes("grid gap-2").style(
                    "grid-template-columns: 130px repeat(7, minmax(150px, 1fr)); min-width: 1200px"
                ):
                    ui.label("עמדה").classes("text-xs muted font-semibold")
                    for i in range(7):
                        ui.label(f"{DAY_NAMES[i]} {fmt_date(week_start + timedelta(days=i))}").classes(
                            "text-xs muted font-semibold text-center"
                        )
                    for position in template:
                        ui.label(position).classes("text-sm font-semibold self-start pt-2")
                        for day_idx in range(7):
                            cell(position, day_idx)

        def cell(position, day_idx):
            ranges = template[position][day_idx]
            with ui.element("div").classes("card p-2 flex flex-col gap-1"):
                for i, (start, end) in enumerate(ranges):
                    with ui.element("div").classes("flex items-center justify-between"):
                        ui.label(ltr(f"{start}–{end}")).classes("mono text-xs")
                        icon_button("x", "הסר טווח", lambda p=position, d=day_idx, idx=i: remove_range(p, d, idx), 12).style(
                            "width: 24px; height: 24px"
                        )
                start_sel = ui.select(HOUR_OPTIONS, label="משעה").props("dense options-dense").classes("w-full")
                end_sel = ui.select(HOUR_OPTIONS, label="עד שעה").props("dense options-dense").classes("w-full")
                with ui.element("div").classes("flex gap-1"):
                    ui.button("הוסף", on_click=lambda p=position, d=day_idx, s=start_sel, e=end_sel: add_range(p, d, s, e)).props(
                        "flat dense no-caps size=sm"
                    )
                    if ranges:
                        ui.button("לכל השבוע", on_click=lambda p=position, d=day_idx: copy_to_week(p, d)).props(
                            "flat dense no-caps size=sm"
                        )

        def add_range(position, day_idx, start_sel, end_sel):
            if not start_sel.value or not end_sel.value:
                toast("יש לבחור שעת התחלה וסיום", kind="warn")
                return
            if start_sel.value == end_sel.value:
                toast("שעת הסיום חייבת להיות שונה משעת ההתחלה", kind="warn")
                return
            template[position][day_idx].append((start_sel.value, end_sel.value))
            grid.refresh()

        def remove_range(position, day_idx, index):
            template[position][day_idx].pop(index)
            grid.refresh()

        def copy_to_week(position, source_day):
            for day_idx in range(7):
                template[position][day_idx] = list(template[position][source_day])
            grid.refresh()

        def fill_all(start, end):
            for position in template:
                for day_idx in range(7):
                    if (start, end) not in template[position][day_idx]:
                        template[position][day_idx].append((start, end))
            grid.refresh()

        grid()

        async def save():
            if not any(ranges for days in template.values() for ranges in days.values()):
                toast("לא הוגדרו טווחי שעות", kind="warn")
                return
            try:
                created = await run.io_bound(create_week_shifts, user_id, week_start, template)
            except Exception as e:
                db_error(e)
                return
            dialog.close()
            toast(f"נוצרו {created} משמרות" if created else "לא נוצרו משמרות חדשות (כבר קיימות)")
            on_done()

        with ui.element("div").classes("flex gap-2 justify-end w-full"):
            button("ביטול", kind="secondary", on_click=dialog.close)
            button("צור משמרות", icon_name="list_plus", on_click=save)

    dialog.open()
