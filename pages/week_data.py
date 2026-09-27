from datetime import timedelta

from db.connection import (
    get_all_assignments,
    get_all_personnel,
    get_all_positions,
    get_all_roles,
    get_all_unavailability,
    get_connection,
    get_shifts_between,
)
from scheduler.rules import SchedulingContext, shift_hours, week_bounds


class WeekData:
    """One user's data for one Sunday-to-Saturday week, loaded in a single connection."""

    def __init__(self, user_id, any_day):
        self.week_start, self.week_end = week_bounds(any_day)
        conn = get_connection()
        try:
            self.shifts = get_shifts_between(conn, user_id, self.week_start, self.week_end)
            self.personnel = get_all_personnel(conn, user_id)
            self.roles = get_all_roles(conn, user_id)
            self.positions = get_all_positions(conn, user_id)
            assignments = get_all_assignments(conn, user_id)
            unavailability = get_all_unavailability(conn, user_id)
        finally:
            conn.close()
        self.role_names = [r["Role_Name"] for r in self.roles]
        self.unavailability = unavailability
        self.ctx = SchedulingContext(self.personnel, assignments, unavailability, self.roles)

    @property
    def days(self):
        return [self.week_start + timedelta(days=i) for i in range(7)]

    @property
    def open_shifts(self):
        return [s for s in self.shifts if s["Assigned_Person_ID"] is None]

    @property
    def filled_count(self):
        return len(self.shifts) - len(self.open_shifts)

    def week_hours(self):
        """Hours each person works in this week."""
        hours = {p["ID"]: 0.0 for p in self.personnel}
        for s in self.shifts:
            if s["Assigned_Person_ID"] in hours:
                hours[s["Assigned_Person_ID"]] += shift_hours(s)
        return hours

    def unavailable_on(self, day):
        return [
            u for u in self.unavailability if u["Start_Date"] <= day <= u["End_Date"]
        ]
