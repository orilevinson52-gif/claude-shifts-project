from nicegui import ui

from db.connection import (
    create_unavailability,
    delete_all_unavailability,
    delete_unavailability,
    get_all_personnel,
    get_all_unavailability,
    get_connection,
)

COLUMNS = [
    {"name": "Full_Name", "label": "שם", "field": "Full_Name", "align": "right"},
    {"name": "Start_Date", "label": "מתאריך", "field": "Start_Date", "align": "center"},
    {"name": "End_Date", "label": "עד תאריך", "field": "End_Date", "align": "center"},
    {"name": "Reason", "label": "סיבה", "field": "Reason", "align": "right"},
    {"name": "actions", "label": "פעולות", "field": "actions", "align": "center"},
]

ACTIONS_SLOT = """
    <q-td :props="props">
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


def format_rows(rows):
    formatted = []
    for row in rows:
        formatted.append(
            {
                "ID": row["ID"],
                "Full_Name": row["Full_Name"],
                "Start_Date": ltr(row["Start_Date"].strftime("%Y-%m-%d")),
                "End_Date": ltr(row["End_Date"].strftime("%Y-%m-%d")),
                "Reason": row["Reason"] or "",
            }
        )
    return formatted


def date_field(label, value=""):
    with ui.input(label, value=value).classes("w-full") as field:
        with field.add_slot("append"):
            icon = ui.icon("edit_calendar").classes("cursor-pointer")
        with ui.menu() as menu:
            ui.date().bind_value(field)
        icon.on("click", menu.open)
    return field


def build(user_id):
    ui.label("אילוצים אישיים - תאריכים שבהם איש צוות אינו זמין (למשל חופשה, טסט וכו')").classes(
        "text-sm text-grey-7"
    )

    with ui.row():
        ui.button("+ הוסף אילוץ", icon="add", color="primary", on_click=lambda: open_form())
        clear_button = ui.button("נקה את כל האילוצים", icon="delete_sweep", color="negative")

    table = ui.table(columns=COLUMNS, rows=[], row_key="ID").classes("w-full")
    table.add_slot("body-cell-actions", ACTIONS_SLOT)
    table.add_slot("body-cell-Start_Date", MONO_SLOT)
    table.add_slot("body-cell-End_Date", MONO_SLOT)

    def refresh():
        try:
            conn = get_connection()
            try:
                rows = get_all_unavailability(conn, user_id)
            finally:
                conn.close()
            table.rows = format_rows(rows)
            table.update()
        except Exception as e:
            ui.notify(f"שגיאת תקשורת עם מסד הנתונים: {e}", color="negative")

    def open_form():
        conn = get_connection()
        try:
            personnel = [(p["ID"], p["Full_Name"]) for p in get_all_personnel(conn, user_id)]
        finally:
            conn.close()

        if not personnel:
            ui.notify("יש להוסיף לפחות איש צוות אחד לפני הוספת אילוץ", color="negative")
            return

        person_options = {pid: name for pid, name in personnel}

        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label("הוספת אילוץ").classes("text-lg font-bold")
            person_select = ui.select(person_options, label="איש צוות", value=personnel[0][0]).classes("w-full")
            start_input = date_field("מתאריך")
            end_input = date_field("עד תאריך")
            reason_input = ui.input("סיבה (לא חובה)").classes("w-full")

            def save():
                if not start_input.value or not end_input.value:
                    ui.notify("יש למלא תאריך התחלה וסיום", color="negative")
                    return
                if end_input.value < start_input.value:
                    ui.notify("תאריך הסיום חייב להיות אחרי תאריך ההתחלה", color="negative")
                    return
                conn = get_connection()
                try:
                    create_unavailability(
                        conn,
                        user_id,
                        person_select.value,
                        start_input.value,
                        end_input.value,
                        reason_input.value.strip() or None,
                    )
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
            ui.label(f'למחוק את האילוץ של "{row["Full_Name"]}"?')

            def do_delete():
                conn = get_connection()
                try:
                    delete_unavailability(conn, user_id, row["ID"])
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
            ui.label("לנקות את כל האילוצים? הפעולה בלתי הפיכה.")

            def do_clear():
                conn = get_connection()
                try:
                    delete_all_unavailability(conn, user_id)
                finally:
                    conn.close()
                dialog.close()
                refresh()
                ui.notify("כל האילוצים נמחקו", color="positive")

            with ui.row().classes("justify-end w-full"):
                ui.button("ביטול", on_click=dialog.close)
                ui.button("נקה", color="negative", on_click=do_clear)
        dialog.open()

    table.on("remove", lambda e: confirm_delete(e.args))
    clear_button.on_click(confirm_clear_all)

    refresh()
