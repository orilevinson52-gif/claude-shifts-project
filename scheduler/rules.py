"""Pure scheduling rules shared by manual assignment (the board) and the dashboard."""

from datetime import timedelta

from config import MIN_REST_HOURS


def week_bounds(day):
    """Sunday-to-Saturday week containing `day`."""
    days_since_sunday = (day.weekday() + 1) % 7
    week_start = day - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def shift_hours(shift):
    return round((shift["End_Time"] - shift["Start_Time"]).total_seconds() / 3600, 2)


def block_reason(shift, person, person_assignments, person_unavailability, role_max):
    """
    Why `person` can't take `shift`, or None if they can.

    shift: Shift_ID, Date, Start_Time, End_Time, Required_Role
    person: ID, Role
    person_assignments: the person's assigned shifts (Shift_ID, Date, Start_Time, End_Time)
    person_unavailability: (start_date, end_date, reason) tuples for the person
    role_max: max shifts per week for the person's role, or None for unlimited
    """
    if person["Role"] != shift["Required_Role"]:
        return f"נדרש {shift['Required_Role']}"

    for start_date, end_date, reason in person_unavailability:
        if start_date <= shift["Date"] <= end_date:
            return f"לא זמין ({reason})" if reason else "לא זמין בתאריך הזה"

    min_rest = timedelta(hours=MIN_REST_HOURS)
    week_start, week_end = week_bounds(shift["Date"])
    weekly_count = 0
    for other in person_assignments:
        if other["Shift_ID"] == shift["Shift_ID"]:
            continue
        if shift["Start_Time"] >= other["End_Time"]:
            gap = shift["Start_Time"] - other["End_Time"]
        elif other["Start_Time"] >= shift["End_Time"]:
            gap = other["Start_Time"] - shift["End_Time"]
        else:
            return "חופף למשמרת אחרת שלו"
        if gap < min_rest:
            return f"פחות מ־{MIN_REST_HOURS} שעות מנוחה"
        if week_start <= other["Date"] <= week_end:
            weekly_count += 1

    if role_max is not None and weekly_count >= role_max:
        return f"הגיע למכסה ({role_max} בשבוע)"
    return None


class SchedulingContext:
    """Everything the rules need about one user's data, loaded once per render."""

    def __init__(self, personnel, assignments, unavailability, roles):
        self.personnel = personnel
        self.people_by_id = {p["ID"]: p for p in personnel}
        self.role_max = {r["Role_Name"]: r["Max_Shifts_Per_Week"] for r in roles}
        self.assignments_by_person = {}
        for a in assignments:
            self.assignments_by_person.setdefault(a["Person_ID"], []).append(a)
        self.unavailability_by_person = {}
        for u in unavailability:
            self.unavailability_by_person.setdefault(u["Person_ID"], []).append(
                (u["Start_Date"], u["End_Date"], u["Reason"])
            )

    def reason(self, shift, person):
        return block_reason(
            shift,
            person,
            self.assignments_by_person.get(person["ID"], []),
            self.unavailability_by_person.get(person["ID"], []),
            self.role_max.get(person["Role"]),
        )

    def candidates(self, shift):
        """People with the shift's role: (person, reason) with available people first, fewest hours first."""
        rows = [
            (p, None if p["ID"] == shift.get("Assigned_Person_ID") else self.reason(shift, p))
            for p in self.personnel
            if p["Role"] == shift["Required_Role"]
        ]
        rows.sort(key=lambda row: (row[1] is not None, float(row[0]["Total_Hours_Done"])))
        return rows

    def open_reason(self, shift):
        """Short explanation for an unassigned shift."""
        same_role = [p for p in self.personnel if p["Role"] == shift["Required_Role"]]
        if not same_role:
            return f"אין אנשי צוות בתפקיד {shift['Required_Role']}"
        reasons = [self.reason(shift, p) for p in same_role]
        if any(r is None for r in reasons):
            return "יש מי שיכול – ממתינה לשיבוץ"
        if any("מכסה" in r for r in reasons):
            return f"כל אנשי ה{shift['Required_Role']} הגיעו למכסה"
        if any("לא זמין" in r for r in reasons):
            return f"אין {shift['Required_Role']} זמין – אילוץ אישי"
        return f"אין {shift['Required_Role']} פנוי – שעות מנוחה"
