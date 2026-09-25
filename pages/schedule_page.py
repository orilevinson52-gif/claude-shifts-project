import plotly.express as px
from nicegui import ui

from db.connection import clear_all_assignments, get_connection, get_full_roster, get_hours_summary
from scheduler.allocator import generate_schedule


def ltr(text):
    return f"⁦{text}⁩"


DAY_NAMES_BY_WEEKDAY = {6: "ראשון", 0: "שני", 1: "שלישי", 2: "רביעי", 3: "חמישי", 4: "שישי", 5: "שבת"}

TIME_SLOT = """
    <q-td :props="props" class="rc-mono" style="text-align:right">
        {{ props.value }}
    </q-td>
"""

CELL_SLOT = """
    <q-td :props="props" :class="props.value === '—' ? 'rc-cell-empty' : ''">
        {{ props.value }}
    </q-td>
"""


def build_tables_by_position(rows):
    positions = {}
    for row in rows:
        positions.setdefault(row["Position_Name"], []).append(row)

    tables = []
    for position in sorted(positions.keys()):
        position_rows = positions[position]

        day_labels = {}  # date_str -> column label
        time_slots = {}  # time_label -> {date_str: assigned_name}
        time_sort_key = {}  # time_label -> time-of-day, for chronological row order
        for row in position_rows:
            date_str = row["Date"].strftime("%Y-%m-%d")
            day_labels[date_str] = f"{DAY_NAMES_BY_WEEKDAY[row['Date'].weekday()]} {row['Date'].strftime('%d/%m')}"
            time_label = f"{row['Start_Time'].strftime('%H:%M')}-{row['End_Time'].strftime('%H:%M')}"
            time_slots.setdefault(time_label, {})[date_str] = row["Assigned_To"] or "—"
            time_sort_key[time_label] = row["Start_Time"].time()

        sorted_dates = sorted(day_labels.keys())
        columns = [{"name": "time_range", "label": "שעות", "field": "time_range", "align": "center"}]
        for date_str in sorted_dates:
            columns.append(
                {"name": date_str, "label": day_labels[date_str], "field": date_str, "align": "center"}
            )

        table_rows = []
        for time_label in sorted(time_slots.keys(), key=lambda t: time_sort_key[t]):
            row_data = {"time_range": ltr(time_label)}
            for date_str in sorted_dates:
                row_data[date_str] = time_slots[time_label].get(date_str, "")
            table_rows.append(row_data)

        tables.append({"position": position, "columns": columns, "rows": table_rows})

    return tables


def build(user_id):
    status_container = ui.column().classes("w-full")

    with ui.row():
        generate_button = ui.button("צור סידור עבודה", icon="auto_awesome", color="primary")
        clear_button = ui.button("נקה משמרות", icon="delete_sweep", color="negative")

    ui.label("סידור העבודה").classes("rc-heading text-lg mt-4")
    roster_container = ui.column().classes("w-full")

    ui.label("איזון עומסים - סך שעות לכל איש צוות").classes("rc-heading text-lg mt-4")
    chart_container = ui.column().classes("w-full")

    def refresh():
        try:
            conn = get_connection()
            try:
                roster_rows = get_full_roster(conn, user_id)
                hours_rows = get_hours_summary(conn, user_id)
            finally:
                conn.close()
        except Exception as e:
            ui.notify(f"שגיאת תקשורת עם מסד הנתונים: {e}", color="negative")
            roster_rows = []
            hours_rows = []

        roster_container.clear()
        tables = build_tables_by_position(roster_rows)
        with roster_container:
            if not tables:
                ui.label("אין משמרות מוגדרות עדיין.")
            for table_info in tables:
                ui.label(table_info["position"]).classes("rc-heading text-base mt-4")
                position_table = ui.table(
                    columns=table_info["columns"], rows=table_info["rows"], row_key="time_range"
                ).classes("w-full")
                position_table.add_slot("body-cell-time_range", TIME_SLOT)
                for column in table_info["columns"]:
                    if column["name"] != "time_range":
                        position_table.add_slot(f"body-cell-{column['name']}", CELL_SLOT)

        chart_container.clear()
        if hours_rows:
            names = [row["Full_Name"] for row in hours_rows]
            hours = [float(row["Total_Hours_Done"]) for row in hours_rows]
            fig = px.bar(
                x=names,
                y=hours,
                labels={"x": "שם", "y": "סך שעות"},
                color_discrete_sequence=["#0d7d8f"],
            )
            fig.update_layout(
                font_family="Heebo, system-ui, sans-serif",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#3a3a38",
            )
            with chart_container:
                ui.plotly(fig).classes("w-full")

    def on_generate():
        conn = get_connection()
        try:
            result = generate_schedule(conn, user_id)
        finally:
            conn.close()

        status_container.clear()
        with status_container:
            if result["assigned"]:
                ui.label(f"שובצו {len(result['assigned'])} משמרות בהצלחה.").classes(
                    "text-white bg-positive rounded p-2"
                )
            if result["unresolved"]:
                ids = ", ".join(str(i) for i in result["unresolved"])
                ui.label(
                    f"לא ניתן היה לשבץ את המשמרות הבאות (אין מועמד זמין שעומד באילוצים): {ids}"
                ).classes("text-white bg-warning rounded p-2")
            if not result["assigned"] and not result["unresolved"]:
                ui.label("כל המשמרות כבר משובצות.").classes("text-white bg-info rounded p-2")

        refresh()

    def on_clear():
        with ui.dialog() as dialog, ui.card():
            ui.label("לנקות את כל המשמרות המשובצות? הפעולה גם תאפס את סך השעות של כל אנשי הצוות.")
            with ui.row().classes("justify-end w-full"):
                ui.button("ביטול", on_click=dialog.close)

                def confirm_clear():
                    conn = get_connection()
                    try:
                        clear_all_assignments(conn, user_id)
                    finally:
                        conn.close()
                    dialog.close()
                    status_container.clear()
                    refresh()
                    ui.notify("כל המשמרות נוקו בהצלחה", color="positive")

                ui.button("נקה", color="negative", on_click=confirm_clear)
        dialog.open()

    generate_button.on_click(on_generate)
    clear_button.on_click(on_clear)

    refresh()
