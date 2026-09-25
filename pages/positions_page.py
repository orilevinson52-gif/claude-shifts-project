import mysql.connector
from nicegui import ui

from db.connection import (
    create_position,
    delete_all_positions,
    delete_position,
    get_all_positions,
    get_all_roles,
    get_connection,
    update_position,
)

COLUMNS = [
    {"name": "Position_Name", "label": "שם עמדה", "field": "Position_Name", "align": "right"},
    {"name": "Required_Role", "label": "תפקיד נדרש", "field": "Required_Role", "align": "center"},
    {"name": "actions", "label": "פעולות", "field": "actions", "align": "center"},
]

ACTIONS_SLOT = """
    <q-td :props="props">
        <q-btn size="sm" flat round icon="edit" @click="() => $parent.$emit('edit', props.row)" />
        <q-btn size="sm" flat round icon="delete" color="negative" @click="() => $parent.$emit('remove', props.row)" />
    </q-td>
"""

ROLE_SLOT = """
    <q-td :props="props">
        <span class="rc-pill">{{ props.value }}</span>
    </q-td>
"""


def build(user_id):
    with ui.row():
        ui.button("+ הוסף עמדה", icon="add", color="primary", on_click=lambda: open_form())
        clear_button = ui.button("נקה את כל העמדות", icon="delete_sweep", color="negative")

    table = ui.table(columns=COLUMNS, rows=[], row_key="Position_Name").classes("w-full")
    table.add_slot("body-cell-actions", ACTIONS_SLOT)
    table.add_slot("body-cell-Required_Role", ROLE_SLOT)

    def refresh():
        try:
            conn = get_connection()
            try:
                rows = get_all_positions(conn, user_id)
            finally:
                conn.close()
            table.rows = rows
            table.update()
        except Exception as e:
            ui.notify(f"שגיאת תקשורת עם מסד הנתונים: {e}", color="negative")

    def open_form(row=None):
        is_edit = row is not None

        conn = get_connection()
        try:
            roles = [r["Role_Name"] for r in get_all_roles(conn, user_id)]
        finally:
            conn.close()

        if not roles:
            ui.notify("יש להוסיף לפחות תפקיד אחד לפני הוספת עמדה", color="negative")
            return

        with ui.dialog() as dialog, ui.card():
            ui.label("עריכת עמדה" if is_edit else "הוספת עמדה").classes("text-lg font-bold")
            name_input = ui.input("שם עמדה", value=row["Position_Name"] if is_edit else "").classes("w-full")
            role_select = ui.select(
                roles,
                label="תפקיד נדרש",
                value=row["Required_Role"] if is_edit and row["Required_Role"] in roles else roles[0],
            ).classes("w-full")

            def save():
                if not name_input.value.strip():
                    ui.notify("יש להזין שם עמדה", color="negative")
                    return
                conn = get_connection()
                try:
                    if is_edit:
                        update_position(conn, user_id, row["Position_Name"], name_input.value.strip(), role_select.value)
                    else:
                        create_position(conn, user_id, name_input.value.strip(), role_select.value)
                except mysql.connector.IntegrityError:
                    ui.notify("עמדה בשם הזה כבר קיימת", color="negative")
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
            ui.label(f'למחוק את העמדה "{row["Position_Name"]}"?')

            def do_delete():
                conn = get_connection()
                try:
                    delete_position(conn, user_id, row["Position_Name"])
                except mysql.connector.IntegrityError:
                    ui.notify("לא ניתן למחוק עמדה שיש לה משמרות משויכות", color="negative")
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
            ui.label("לנקות את כל העמדות? הפעולה בלתי הפיכה.")

            def do_clear():
                conn = get_connection()
                try:
                    delete_all_positions(conn, user_id)
                except mysql.connector.IntegrityError:
                    ui.notify("לא ניתן לנקות עמדות שיש להן משמרות משויכות", color="negative")
                    dialog.close()
                    return
                finally:
                    conn.close()
                dialog.close()
                refresh()
                ui.notify("כל העמדות נמחקו", color="positive")

            with ui.row().classes("justify-end w-full"):
                ui.button("ביטול", on_click=dialog.close)
                ui.button("נקה", color="negative", on_click=do_clear)
        dialog.open()

    table.on("edit", lambda e: open_form(e.args))
    table.on("remove", lambda e: confirm_delete(e.args))
    clear_button.on_click(confirm_clear_all)

    refresh()
