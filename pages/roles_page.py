import mysql.connector
from nicegui import ui

from db.connection import (
    create_role,
    delete_all_roles,
    delete_role,
    get_all_roles,
    get_connection,
    update_role,
)

COLUMNS = [
    {"name": "Role_Name", "label": "שם תפקיד", "field": "Role_Name", "align": "right"},
    {
        "name": "Max_Shifts_Per_Week",
        "label": "מקסימום משמרות בשבוע",
        "field": "Max_Shifts_Per_Week",
        "align": "center",
    },
    {"name": "actions", "label": "פעולות", "field": "actions", "align": "center"},
]


def format_rows(rows):
    return [
        {
            "Role_Name": row["Role_Name"],
            "Max_Shifts_Per_Week": row["Max_Shifts_Per_Week"]
            if row["Max_Shifts_Per_Week"] is not None
            else "ללא הגבלה",
        }
        for row in rows
    ]

ACTIONS_SLOT = """
    <q-td :props="props">
        <q-btn size="sm" flat round icon="edit" @click="() => $parent.$emit('edit', props.row)" />
        <q-btn size="sm" flat round icon="delete" color="negative" @click="() => $parent.$emit('remove', props.row)" />
    </q-td>
"""


def build():
    with ui.row():
        ui.button("+ הוסף תפקיד", icon="add", color="primary", on_click=lambda: open_form())
        clear_button = ui.button("נקה את כל התפקידים", icon="delete_sweep", color="negative")

    table = ui.table(columns=COLUMNS, rows=[], row_key="Role_Name").classes("w-full")
    table.add_slot("body-cell-actions", ACTIONS_SLOT)

    raw_rows_by_name = {}

    def refresh():
        conn = get_connection()
        try:
            rows = get_all_roles(conn)
        finally:
            conn.close()
        raw_rows_by_name.clear()
        raw_rows_by_name.update({r["Role_Name"]: r for r in rows})
        table.rows = format_rows(rows)
        table.update()

    def open_form(row=None):
        is_edit = row is not None
        raw = raw_rows_by_name.get(row["Role_Name"]) if is_edit else None

        with ui.dialog() as dialog, ui.card():
            ui.label("עריכת תפקיד" if is_edit else "הוספת תפקיד").classes("text-lg font-bold")
            name_input = ui.input("שם תפקיד", value=raw["Role_Name"] if is_edit else "").classes("w-full")
            unlimited_checkbox = ui.checkbox(
                "ללא הגבלת משמרות בשבוע",
                value=not is_edit or raw["Max_Shifts_Per_Week"] is None,
            )
            max_shifts_input = ui.number(
                "מקסימום משמרות בשבוע",
                value=raw["Max_Shifts_Per_Week"] if is_edit and raw["Max_Shifts_Per_Week"] is not None else 1,
                min=1,
                format="%d",
            ).classes("w-full")
            max_shifts_input.bind_enabled_from(unlimited_checkbox, "value", backward=lambda v: not v)

            def save():
                if not name_input.value.strip():
                    ui.notify("יש להזין שם תפקיד", color="negative")
                    return
                max_shifts = None if unlimited_checkbox.value else int(max_shifts_input.value)
                conn = get_connection()
                try:
                    if is_edit:
                        update_role(conn, raw["Role_Name"], name_input.value.strip(), max_shifts)
                    else:
                        create_role(conn, name_input.value.strip(), max_shifts)
                except mysql.connector.IntegrityError:
                    ui.notify("תפקיד בשם הזה כבר קיים", color="negative")
                    return
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
            ui.label(f'למחוק את התפקיד "{row["Role_Name"]}"?')

            def do_delete():
                conn = get_connection()
                try:
                    delete_role(conn, row["Role_Name"])
                except mysql.connector.IntegrityError:
                    ui.notify("לא ניתן למחוק תפקיד שמשויך לאנשי צוות או לעמדות", color="negative")
                    dialog.close()
                    return
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
            ui.label("לנקות את כל התפקידים? הפעולה בלתי הפיכה.")

            def do_clear():
                conn = get_connection()
                try:
                    delete_all_roles(conn)
                except mysql.connector.IntegrityError:
                    ui.notify("לא ניתן לנקות תפקידים שמשויכים לאנשי צוות או לעמדות", color="negative")
                    dialog.close()
                    return
                finally:
                    conn.close()
                dialog.close()
                refresh()
                ui.notify("כל התפקידים נמחקו", color="positive")

            with ui.row().classes("justify-end w-full"):
                ui.button("ביטול", on_click=dialog.close)
                ui.button("נקה", color="negative", on_click=do_clear)
        dialog.open()

    table.on("edit", lambda e: open_form(e.args))
    table.on("remove", lambda e: confirm_delete(e.args))
    clear_button.on_click(confirm_clear_all)

    refresh()
