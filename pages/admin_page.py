from nicegui import ui

from auth import RegistrationError, is_admin, reset_password
from db.connection import delete_user_and_data, get_all_users_with_stats, get_connection, get_user_by_id

COLUMNS = [
    {"name": "Username", "label": "שם משתמש", "field": "Username", "align": "right"},
    {"name": "Created_At", "label": "נרשם בתאריך", "field": "Created_At", "align": "center"},
    {"name": "Personnel_Count", "label": "אנשי צוות", "field": "Personnel_Count", "align": "center"},
    {"name": "Positions_Count", "label": "עמדות", "field": "Positions_Count", "align": "center"},
    {"name": "Shifts_Count", "label": "משמרות", "field": "Shifts_Count", "align": "center"},
    {"name": "actions", "label": "פעולות", "field": "actions", "align": "center"},
]

ACTIONS_SLOT = """
    <q-td :props="props">
        <q-btn size="sm" flat round icon="lock_reset" @click="() => $parent.$emit('reset', props.row)">
            <q-tooltip>איפוס סיסמה</q-tooltip>
        </q-btn>
        <q-btn v-if="!props.row.Is_Self" size="sm" flat round icon="delete" color="negative"
               @click="() => $parent.$emit('remove', props.row)">
            <q-tooltip>מחיקת משתמש</q-tooltip>
        </q-btn>
    </q-td>
"""

MONO_SLOT = """
    <q-td :props="props" class="rc-mono">
        {{ props.value }}
    </q-td>
"""


def ltr(text):
    return f"⁦{text}⁩"


def format_rows(rows, admin_user_id):
    return [
        {
            "ID": row["ID"],
            "Username": row["Username"],
            "Created_At": ltr(row["Created_At"].strftime("%Y-%m-%d %H:%M")),
            "Personnel_Count": row["Personnel_Count"],
            "Positions_Count": row["Positions_Count"],
            "Shifts_Count": row["Shifts_Count"],
            "Is_Self": row["ID"] == admin_user_id,
        }
        for row in rows
    ]


def build(admin_user_id):
    ui.label("ניהול משתמשים").classes("rc-heading text-lg")
    summary_label = ui.label().classes("text-sm text-grey-7 q-mb-md")

    table = ui.table(columns=COLUMNS, rows=[], row_key="ID").classes("w-full")
    table.add_slot("body-cell-actions", ACTIONS_SLOT)
    table.add_slot("body-cell-Created_At", MONO_SLOT)

    def still_admin():
        # Re-checked on every action, not just when the tab was drawn
        conn = get_connection()
        try:
            me = get_user_by_id(conn, admin_user_id)
        finally:
            conn.close()
        if not me or not is_admin(me["Username"]):
            ui.notify("אין הרשאה", color="negative")
            return False
        return True

    def refresh():
        try:
            conn = get_connection()
            try:
                rows = get_all_users_with_stats(conn)
            finally:
                conn.close()
            table.rows = format_rows(rows, admin_user_id)
            table.update()
            summary_label.set_text(f"סה״כ {len(rows)} משתמשים רשומים")
        except Exception as e:
            ui.notify(f"שגיאת תקשורת עם מסד הנתונים: {e}", color="negative")

    def open_reset(row):
        with ui.dialog() as dialog, ui.card().classes("w-96"):
            ui.label(f'איפוס סיסמה ל"{row["Username"]}"').classes("text-lg font-bold")
            password_input = ui.input("סיסמה חדשה (לפחות 8 תווים)", password=True).classes("w-full")

            def save():
                if not still_admin():
                    dialog.close()
                    return
                try:
                    reset_password(row["ID"], password_input.value)
                except RegistrationError as e:
                    ui.notify(str(e), color="negative")
                    return
                dialog.close()
                ui.notify("הסיסמה עודכנה. מסור אותה למשתמש.", color="positive")

            with ui.row().classes("justify-end w-full"):
                ui.button("ביטול", on_click=dialog.close)
                ui.button("עדכן", color="primary", on_click=save)
        dialog.open()

    def confirm_delete(row):
        if row["ID"] == admin_user_id:
            return
        with ui.dialog() as dialog, ui.card():
            ui.label(
                f'למחוק את המשתמש "{row["Username"]}" ואת כל הנתונים שלו '
                f'({row["Personnel_Count"]} אנשי צוות, {row["Shifts_Count"]} משמרות)? הפעולה בלתי הפיכה.'
            )

            def do_delete():
                if not still_admin():
                    dialog.close()
                    return
                conn = get_connection()
                try:
                    delete_user_and_data(conn, row["ID"])
                finally:
                    conn.close()
                dialog.close()
                refresh()
                ui.notify("המשתמש נמחק", color="positive")

            with ui.row().classes("justify-end w-full"):
                ui.button("ביטול", on_click=dialog.close)
                ui.button("מחק", color="negative", on_click=do_delete)
        dialog.open()

    table.on("reset", lambda e: open_reset(e.args))
    table.on("remove", lambda e: confirm_delete(e.args))

    ui.button("רענן", icon="refresh", on_click=refresh).props("flat").classes("q-mt-sm")

    refresh()
