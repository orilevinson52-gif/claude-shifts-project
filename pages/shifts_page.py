from datetime import datetime, timedelta

from nicegui import ui

from db.connection import (
    create_shift,
    delete_all_shifts,
    delete_shift,
    get_all_positions,
    get_all_shifts,
    get_connection,
    update_shift,
)

DAY_NAMES = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]
HOUR_OPTIONS = [f"{h:02d}:00" for h in range(24)]

COLUMNS = [
    {"name": "Date", "label": "תאריך", "field": "Date", "align": "center"},
    {"name": "Start_Time", "label": "התחלה", "field": "Start_Time", "align": "center"},
    {"name": "End_Time", "label": "סיום", "field": "End_Time", "align": "center"},
    {"name": "Position_Name", "label": "עמדה", "field": "Position_Name", "align": "right"},
    {"name": "Assigned_To", "label": "שובץ ל", "field": "Assigned_To", "align": "right"},
    {"name": "actions", "label": "פעולות", "field": "actions", "align": "center"},
]

ACTIONS_SLOT = """
    <q-td :props="props">
        <q-btn size="sm" flat round icon="edit" @click="() => $parent.$emit('edit', props.row)" />
        <q-btn size="sm" flat round icon="delete" color="negative" @click="() => $parent.$emit('remove', props.row)" />
    </q-td>
"""

MONO_SLOT = """
    <q-td :props="props" class="rc-mono">
        {{ props.value }}
    </q-td>
"""


def ltr(text):
    return f"⁦{text}⁩"


def week_start_of(day):
    days_since_sunday = (day.weekday() + 1) % 7
    return day - timedelta(days=days_since_sunday)


def format_rows(rows):
    formatted = []
    for row in rows:
        formatted.append(
            {
                "Shift_ID": row["Shift_ID"],
                "Date": ltr(row["Date"].strftime("%Y-%m-%d")),
                "Start_Time": ltr(row["Start_Time"].strftime("%Y-%m-%d %H:%M")),
                "End_Time": ltr(row["End_Time"].strftime("%Y-%m-%d %H:%M")),
                "Position_Name": row["Position_Name"],
                "Assigned_To": row["Assigned_To"] or "לא שובץ",
            }
        )
    return formatted


def date_time_field(label, value=""):
    with ui.input(label, value=value).classes("w-full") as field:
        with field.add_slot("append"):
            icon = ui.icon("edit_calendar" if "תאריך" in label else "access_time").classes("cursor-pointer")
        with ui.menu() as menu:
            if "תאריך" in label:
                ui.date().bind_value(field)
            else:
                ui.time().bind_value(field)
        icon.on("click", menu.open)
    return field


def build():
    week_state = {"start": None}
    template = {}  # {position_name: {day_index(0-6): [(start_str, end_str), ...]}}

    # --- Week template builder ---

    ui.label("בניית משמרות לשבוע").classes("rc-heading text-lg")
    ui.label("בחר תאריך כלשהו בתוך השבוע הרצוי, הגדר שעות לכל עמדה בכל יום, ולחץ \"צור משמרות לשבוע\"").classes(
        "text-sm text-grey-7 q-mb-md"
    )

    week_picker = date_time_field("תאריך בתוך השבוע", "")
    week_label = ui.label().classes("rc-mono text-sm q-mt-sm q-mb-md")

    @ui.refreshable
    def render_grid():
        if week_state["start"] is None:
            ui.label("בחר תאריך כדי לטעון שבוע.").classes("text-grey-7")
            return

        conn = get_connection()
        try:
            positions = [p["Position_Name"] for p in get_all_positions(conn)]
        finally:
            conn.close()

        if not positions:
            ui.label("יש להוסיף לפחות עמדה אחת לפני בניית משמרות.").classes("text-grey-7")
            return

        for position in positions:
            template.setdefault(position, {i: [] for i in range(7)})

        scroll_wrapper = ui.row().classes("w-full").style("overflow-x: auto")
        with scroll_wrapper, ui.grid(columns=8).classes("gap-2").style("min-width: 1300px"):
            ui.label("עמדה").classes("text-xs text-grey-7 font-bold")
            for day_idx in range(7):
                day_date = week_state["start"] + timedelta(days=day_idx)
                ui.label(f"{DAY_NAMES[day_idx]} {day_date.strftime('%d/%m')}").classes(
                    "rc-mono text-xs text-grey-7 font-bold text-center"
                )

            for position in positions:
                ui.label(position).classes("text-sm self-start q-pt-xs")
                for day_idx in range(7):
                    with ui.column().classes("gap-1 border rounded p-2").style("min-width: 160px"):
                        for i, (start_val, end_val) in enumerate(template[position][day_idx]):
                            with ui.row().classes("items-center justify-between gap-1 no-wrap w-full"):
                                ui.label(f"{start_val}-{end_val}").classes("rc-mono text-xs")
                                ui.button(
                                    icon="close",
                                    on_click=lambda p=position, d=day_idx, idx=i: remove_range(p, d, idx),
                                ).props("flat dense round size=xs")

                        start_input = ui.select(HOUR_OPTIONS, label="משעה").classes("w-full").props(
                            "dense options-dense"
                        )
                        end_input = ui.select(HOUR_OPTIONS, label="עד שעה").classes("w-full").props(
                            "dense options-dense"
                        )
                        ui.button(
                            "הוסף",
                            icon="add",
                            on_click=lambda p=position, d=day_idx, s=start_input, e=end_input: add_range(
                                p, d, s, e
                            ),
                        ).props("flat dense size=sm").classes("text-xs w-full")

                        if template[position][day_idx]:
                            ui.button(
                                "העתק לכל השבוע",
                                icon="content_copy",
                                on_click=lambda p=position, d=day_idx: copy_day_to_week(p, d),
                            ).props("flat dense size=sm").classes("text-xs w-full")

    def add_range(position, day_idx, start_input, end_input):
        if not start_input.value or not end_input.value:
            ui.notify("יש לבחור שעת התחלה וסיום", color="negative")
            return
        template[position][day_idx].append((start_input.value, end_input.value))
        start_input.value = None
        end_input.value = None
        render_grid.refresh()

    def remove_range(position, day_idx, index):
        template[position][day_idx].pop(index)
        render_grid.refresh()

    def copy_day_to_week(position, source_day_idx):
        ranges_copy = list(template[position][source_day_idx])
        for day_idx in range(7):
            if day_idx != source_day_idx:
                template[position][day_idx] = list(ranges_copy)
        render_grid.refresh()
        ui.notify("השעות הועתקו לכל ימי השבוע", color="positive")

    def load_week():
        if not week_picker.value:
            ui.notify("יש לבחור תאריך", color="negative")
            return
        picked = datetime.strptime(week_picker.value, "%Y-%m-%d").date()
        week_state["start"] = week_start_of(picked)
        week_end = week_state["start"] + timedelta(days=6)
        week_number = week_state["start"].isocalendar()[1]
        week_label.set_text(
            f"שבוע {week_number} · {week_state['start'].strftime('%Y-%m-%d')} - {week_end.strftime('%Y-%m-%d')}"
        )
        template.clear()
        render_grid.refresh()

    with ui.row().classes("items-end gap-2"):
        ui.button("טען שבוע", icon="event", on_click=load_week)

    render_grid()

    def generate_week_shifts():
        if week_state["start"] is None:
            ui.notify("יש לטעון שבוע קודם", color="negative")
            return

        conn = get_connection()
        try:
            existing = get_all_shifts(conn)
            existing_keys = {
                (row["Date"], row["Position_Name"], row["Start_Time"].strftime("%H:%M")) for row in existing
            }

            created = 0
            for position, days in template.items():
                for day_idx, ranges in days.items():
                    shift_date = week_state["start"] + timedelta(days=day_idx)
                    for start_val, end_val in ranges:
                        if (shift_date, position, start_val) in existing_keys:
                            continue
                        start_dt = datetime.combine(shift_date, datetime.strptime(start_val, "%H:%M").time())
                        end_dt = datetime.combine(shift_date, datetime.strptime(end_val, "%H:%M").time())
                        if end_dt <= start_dt:
                            end_dt += timedelta(days=1)
                        create_shift(conn, shift_date, start_dt, end_dt, position)
                        created += 1
        finally:
            conn.close()

        ui.notify(f"נוצרו {created} משמרות חדשות לשבוע" if created else "לא נוצרו משמרות חדשות (כבר קיימות)", color="positive")
        refresh()

    ui.button("צור משמרות לשבוע", icon="playlist_add", color="primary", on_click=generate_week_shifts).classes(
        "q-mt-md q-mb-lg"
    )

    ui.separator().classes("q-mb-md")

    # --- Existing shifts list ---

    ui.label("כל המשמרות").classes("rc-heading text-lg")

    with ui.row():
        clear_button = ui.button("מחק את כל המשמרות", icon="delete_sweep", color="negative")

    table = ui.table(columns=COLUMNS, rows=[], row_key="Shift_ID").classes("w-full")
    table.add_slot("body-cell-actions", ACTIONS_SLOT)
    table.add_slot("body-cell-Date", MONO_SLOT)
    table.add_slot("body-cell-Start_Time", MONO_SLOT)
    table.add_slot("body-cell-End_Time", MONO_SLOT)

    def refresh():
        try:
            conn = get_connection()
            try:
                rows = get_all_shifts(conn)
            finally:
                conn.close()
            table.rows = format_rows(rows)
            table.update()
        except Exception as e:
            ui.notify(f"שגיאת תקשורת עם מסד הנתונים: {e}", color="negative")

    def open_form(row=None):
        is_edit = row is not None

        conn = get_connection()
        try:
            positions = [p["Position_Name"] for p in get_all_positions(conn)]
        finally:
            conn.close()

        if not positions:
            ui.notify("יש להוסיף לפחות עמדה אחת לפני יצירת משמרת", color="negative")
            return

        date_val = row["Date"].strip("⁦⁩") if is_edit else ""
        start_val = row["Start_Time"].strip("⁦⁩").split(" ")[1] if is_edit else ""
        end_val = row["End_Time"].strip("⁦⁩").split(" ")[1] if is_edit else ""

        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("עריכת משמרת" if is_edit else "הוספת משמרת").classes("text-lg font-bold")
            date_input = date_time_field("תאריך", date_val)
            start_input = date_time_field("שעת התחלה", start_val)
            end_input = date_time_field("שעת סיום", end_val)
            position_select = ui.select(
                positions,
                label="עמדה",
                value=row["Position_Name"] if is_edit and row["Position_Name"] in positions else positions[0],
            ).classes("w-full")

            def save():
                try:
                    start_dt = datetime.strptime(f"{date_input.value} {start_input.value}", "%Y-%m-%d %H:%M")
                    end_dt = datetime.strptime(f"{date_input.value} {end_input.value}", "%Y-%m-%d %H:%M")
                except ValueError:
                    ui.notify("יש למלא תאריך ושעות תקינים", color="negative")
                    return
                if end_dt <= start_dt:
                    end_dt += timedelta(days=1)

                conn = get_connection()
                try:
                    if is_edit:
                        update_shift(conn, row["Shift_ID"], date_input.value, start_dt, end_dt, position_select.value)
                    else:
                        create_shift(conn, date_input.value, start_dt, end_dt, position_select.value)
                finally:
                    conn.close()
                dialog.close()
                refresh()
                ui.notify("נשמר בהצלחה", color="positive")

            with ui.row().classes("justify-end w-full"):
                ui.button("ביטול", on_click=dialog.close)
                ui.button("שמור", color="primary", on_click=save)
        dialog.open()

    def confirm_delete(row):
        with ui.dialog() as dialog, ui.card():
            ui.label(f'למחוק את משמרת {row["Shift_ID"]}?')

            def do_delete():
                conn = get_connection()
                try:
                    delete_shift(conn, row["Shift_ID"])
                finally:
                    conn.close()
                dialog.close()
                refresh()
                ui.notify("נמחק בהצלחה", color="positive")

            with ui.row().classes("justify-end w-full"):
                ui.button("ביטול", on_click=dialog.close)
                ui.button("מחק", color="negative", on_click=do_delete)
        dialog.open()

    def confirm_clear_all():
        with ui.dialog() as dialog, ui.card():
            ui.label("למחוק את כל המשמרות מהמערכת (כולל היסטוריית השיבוצים)? הפעולה בלתי הפיכה.")

            def do_clear():
                conn = get_connection()
                try:
                    delete_all_shifts(conn)
                finally:
                    conn.close()
                dialog.close()
                refresh()
                ui.notify("כל המשמרות נמחקו", color="positive")

            with ui.row().classes("justify-end w-full"):
                ui.button("ביטול", on_click=dialog.close)
                ui.button("מחק", color="negative", on_click=do_clear)
        dialog.open()

    table.on("edit", lambda e: open_form(e.args))
    table.on("remove", lambda e: confirm_delete(e.args))
    clear_button.on_click(confirm_clear_all)

    refresh()
