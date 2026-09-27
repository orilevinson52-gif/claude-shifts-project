from datetime import date, datetime

from scheduler.rules import SchedulingContext, block_reason, week_bounds

GUARD = {"ID": 1, "Full_Name": "רועי", "Role": "מאבטח", "Total_Hours_Done": 0}


def shift(shift_id, day, start_hour, end_hour, role="מאבטח", assigned=None):
    return {
        "Shift_ID": shift_id,
        "Date": date(2026, 9, day),
        "Start_Time": datetime(2026, 9, day, start_hour),
        "End_Time": datetime(2026, 9, day, end_hour),
        "Required_Role": role,
        "Assigned_Person_ID": assigned,
    }


def test_week_runs_sunday_to_saturday():
    assert week_bounds(date(2026, 9, 30)) == (date(2026, 9, 27), date(2026, 10, 3))
    assert week_bounds(date(2026, 9, 27)) == (date(2026, 9, 27), date(2026, 10, 3))


def test_available_person_has_no_reason():
    assert block_reason(shift(1, 28, 6, 14), GUARD, [], [], None) is None


def test_wrong_role_is_blocked():
    assert block_reason(shift(1, 28, 6, 14, role="סמבצית"), GUARD, [], [], None) == "נדרש סמבצית"


def test_unavailability_blocks_with_reason():
    reason = block_reason(shift(1, 28, 6, 14), GUARD, [], [(date(2026, 9, 28), date(2026, 9, 29), "מילואים")], None)
    assert reason == "לא זמין (מילואים)"


def test_back_to_back_shifts_break_rest_rule():
    earlier = shift(2, 28, 6, 14)
    assert "מנוחה" in block_reason(shift(1, 28, 14, 22), GUARD, [earlier], [], None)


def test_exactly_eight_hours_rest_is_allowed():
    earlier = shift(2, 28, 6, 14)
    assert block_reason(shift(1, 28, 22, 23), GUARD, [earlier], [], None) is None


def test_overlap_is_blocked():
    other = shift(2, 28, 10, 18)
    assert "חופף" in block_reason(shift(1, 28, 6, 14), GUARD, [other], [], None)


def test_weekly_cap_counts_only_the_same_week():
    this_week = [shift(10 + d, d, 6, 14) for d in (27, 28)]
    last_week = [shift(20, 20, 6, 14)]
    assert "מכסה" in block_reason(shift(1, 30, 6, 14), GUARD, this_week + last_week, [], 2)
    assert block_reason(shift(1, 30, 6, 14), GUARD, this_week[:1] + last_week, [], 2) is None


def test_the_shift_itself_is_ignored():
    same = shift(1, 28, 6, 14)
    assert block_reason(same, GUARD, [same], [], 1) is None


def make_ctx(assignments=(), unavailability=(), personnel=None):
    personnel = personnel or [
        GUARD,
        {"ID": 2, "Full_Name": "נועה", "Role": "מאבטח", "Total_Hours_Done": 30},
        {"ID": 3, "Full_Name": "מיכל", "Role": "סמבצית", "Total_Hours_Done": 0},
    ]
    roles = [{"Role_Name": "מאבטח", "Max_Shifts_Per_Week": None}, {"Role_Name": "סמבצית", "Max_Shifts_Per_Week": 5}]
    return SchedulingContext(personnel, list(assignments), list(unavailability), roles)


def test_candidates_only_same_role_available_first_then_fewest_hours():
    ctx = make_ctx(unavailability=[{"Person_ID": 1, "Start_Date": date(2026, 9, 28), "End_Date": date(2026, 9, 28), "Reason": "טסט"}])
    rows = ctx.candidates(shift(1, 28, 6, 14))
    assert [p["ID"] for p, _ in rows] == [2, 1]
    assert rows[0][1] is None and rows[1][1] == "לא זמין (טסט)"


def test_current_assignee_is_never_blocked_in_candidates():
    busy = {"Shift_ID": 1, "Person_ID": 1, "Date": date(2026, 9, 28),
            "Start_Time": datetime(2026, 9, 28, 6), "End_Time": datetime(2026, 9, 28, 14)}
    rows = dict((p["ID"], r) for p, r in make_ctx(assignments=[busy]).candidates(shift(1, 28, 6, 14, assigned=1)))
    assert rows[1] is None


def test_open_reason_explains_why_nobody_fits():
    assert make_ctx().open_reason(shift(1, 28, 6, 14)).startswith("יש מי")
    assert "אין אנשי צוות" in make_ctx().open_reason(shift(1, 28, 6, 14, role="לוחם"))
    away = [{"Person_ID": pid, "Start_Date": date(2026, 9, 28), "End_Date": date(2026, 9, 28), "Reason": None}
            for pid in (1, 2)]
    assert "אילוץ" in make_ctx(unavailability=away).open_reason(shift(1, 28, 6, 14))
