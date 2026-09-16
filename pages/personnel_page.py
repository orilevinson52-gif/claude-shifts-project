from nicegui import ui

from db.connection import (
    create_person,
    delete_all_personnel,
    delete_person,
    get_all_personnel,
    get_all_roles,
    get_connection,
    update_person,
)

COLUMNS = [
    {"name": "Full_Name", "label": "שם מלא", "field": "Full_Name", "align": "right"},
    {"name": "Role", "label": "תפקיד", "field": "Role", "align": "center"},
    {"name": "Total_Hours_Done", "label": "סך שעות", "field": "Total_Hours_Done", "align": "center"},
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

HOURS_SLOT = """
    <q-td :props="props" class="rc-mono">
        {{ props.value }}
    </q-td>
"""


def build():
    with ui.row():
        ui.button("+ הוסף איש צוות", icon="add", color="primary", on_click=lambda: open_form())
        clear_button = ui.button("נקה את כל אנשי הצוות", icon="delete_sweep", color="negative")

    table = ui.table(columns=COLUMNS, rows=[], row_key="ID").classes("w-full")
    table.add_slot("body-cell-actions", ACTIONS_SLOT)
    table.add_slot("body-cell-Role", ROLE_SLOT)
    table.add_slot("body-cell-Total_Hours_Done", HOURS_SLOT)

    def refresh():
        conn = get_connection()
        try:
            rows = get_all_personnel(conn)
        finally:
            conn.close()
        table.rows = rows
        table.update()

    def open_form(row=None):
        is_edit = row is not None

        conn = get_connection()
        try:
            roles = [r["Role_Name"] for r in get_all_roles(conn)]
        finally:
            conn.close()

        if not roles:
            ui.notify("יש להוסיף לפחות תפקיד אחד לפני הוספת איש צוות", color="negative")
            return

        with ui.dialog() as dialog, ui.card():
            ui.label("עריכת איש צוות" if is_edit else "הוספת איש צוות").classes("text-lg font-bold")
            name_input = ui.input("שם מלא", value=row["Full_Name"] if is_edit else "").classes("w-full")
            role_select = ui.select(
                roles,
                label="תפקיד",
                value=row["Role"] if is_edit and row["Role"] in roles else roles[0],
            ).classes("w-full")

            def save():
                if not name_input.value.strip():
                    ui.notify("יש להזין שם מלא", color="negative")
                    return
                conn = get_connection()
                try:
                    if is_edit:
                        update_person(conn, row["ID"], name_input.value.strip(), role_select.value)
                    else:
                        create_person(conn, name_input.value.strip(), role_select.value)
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
            ui.label(f'למחוק את "{row["Full_Name"]}"?')

            def do_delete():
                conn = get_connection()
                try:
                    delete_person(conn, row["ID"])
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
            ui.label("לנקות את כל אנשי הצוות? הפעולה בלתי הפיכה.")

            def do_clear():
                conn = get_connection()
                try:
                    delete_all_personnel(conn)
                finally:
                    conn.close()
                dialog.close()
                refresh()
                ui.notify("כל אנשי הצוות נמחקו", color="positive")

            with ui.row().classes("justify-end w-full"):
                ui.button("ביטול", on_click=dialog.close)
                ui.button("נקה", color="negative", on_click=do_clear)
        dialog.open()

    table.on("edit", lambda e: open_form(e.args))
    table.on("remove", lambda e: confirm_delete(e.args))
    clear_button.on_click(confirm_clear_all)

    refresh()
