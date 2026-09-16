from datetime import date, datetime

import scheduler.allocator as allocator


class FakeConn:
    def __init__(self):
        self.committed = False
        self.rolled_back = False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


SAMPLE_SHIFT = {
    "Shift_ID": 1,
    "Position_Name": "שער ראשי",
    "Date": date(2026, 8, 26),
    "Start_Time": datetime(2026, 8, 26, 14, 0),
    "End_Time": datetime(2026, 8, 26, 22, 0),
}


def patch_defaults(monkeypatch):
    """No unavailability, no weekly cap, unless a test overrides these."""
    monkeypatch.setattr(allocator, "get_role_max_shifts_per_week", lambda conn, role: None)
    monkeypatch.setattr(allocator, "get_unavailability_ranges_for_person", lambda conn, pid: [])
    monkeypatch.setattr(allocator, "get_weekly_shift_count", lambda conn, pid, start, end: 0)


def find_candidate(shift=SAMPLE_SHIFT):
    return allocator.find_best_candidate(None, shift, {}, {}, {}, {}, {})


def test_exact_8_hour_rest_is_allowed(monkeypatch):
    patch_defaults(monkeypatch)
    monkeypatch.setattr(allocator, "get_position_required_role", lambda conn, pos: "Fighter")
    monkeypatch.setattr(
        allocator,
        "get_available_personnel",
        lambda conn, role: [{"ID": 1, "Full_Name": "A", "Total_Hours_Done": 0}],
    )
    monkeypatch.setattr(
        allocator, "get_last_shift_end", lambda conn, pid: datetime(2026, 8, 26, 6, 0)
    )

    assert find_candidate() == 1


def test_less_than_8_hour_rest_is_rejected(monkeypatch):
    patch_defaults(monkeypatch)
    monkeypatch.setattr(allocator, "get_position_required_role", lambda conn, pos: "Fighter")
    monkeypatch.setattr(
        allocator,
        "get_available_personnel",
        lambda conn, role: [{"ID": 1, "Full_Name": "A", "Total_Hours_Done": 0}],
    )
    monkeypatch.setattr(
        allocator, "get_last_shift_end", lambda conn, pid: datetime(2026, 8, 26, 6, 30)
    )

    assert find_candidate() is None


def test_lowest_hours_candidate_is_chosen(monkeypatch):
    patch_defaults(monkeypatch)
    monkeypatch.setattr(allocator, "get_position_required_role", lambda conn, pos: "Fighter")
    monkeypatch.setattr(
        allocator,
        "get_available_personnel",
        lambda conn, role: [
            {"ID": 1, "Full_Name": "A", "Total_Hours_Done": 20},
            {"ID": 2, "Full_Name": "B", "Total_Hours_Done": 5},
        ],
    )
    monkeypatch.setattr(allocator, "get_last_shift_end", lambda conn, pid: None)

    assert find_candidate() == 2


def test_no_available_candidates_returns_none(monkeypatch):
    patch_defaults(monkeypatch)
    monkeypatch.setattr(allocator, "get_position_required_role", lambda conn, pos: "Fighter")
    monkeypatch.setattr(allocator, "get_available_personnel", lambda conn, role: [])

    assert find_candidate() is None


def test_unavailable_person_on_shift_date_is_excluded(monkeypatch):
    monkeypatch.setattr(allocator, "get_position_required_role", lambda conn, pos: "Fighter")
    monkeypatch.setattr(
        allocator,
        "get_available_personnel",
        lambda conn, role: [{"ID": 1, "Full_Name": "A", "Total_Hours_Done": 0}],
    )
    monkeypatch.setattr(allocator, "get_last_shift_end", lambda conn, pid: None)
    monkeypatch.setattr(allocator, "get_role_max_shifts_per_week", lambda conn, role: None)
    monkeypatch.setattr(allocator, "get_weekly_shift_count", lambda conn, pid, start, end: 0)
    monkeypatch.setattr(
        allocator,
        "get_unavailability_ranges_for_person",
        lambda conn, pid: [(date(2026, 8, 26), date(2026, 8, 26))],
    )

    assert find_candidate() is None


def test_person_available_outside_unavailability_range(monkeypatch):
    monkeypatch.setattr(allocator, "get_position_required_role", lambda conn, pos: "Fighter")
    monkeypatch.setattr(
        allocator,
        "get_available_personnel",
        lambda conn, role: [{"ID": 1, "Full_Name": "A", "Total_Hours_Done": 0}],
    )
    monkeypatch.setattr(allocator, "get_last_shift_end", lambda conn, pid: None)
    monkeypatch.setattr(allocator, "get_role_max_shifts_per_week", lambda conn, role: None)
    monkeypatch.setattr(allocator, "get_weekly_shift_count", lambda conn, pid, start, end: 0)
    monkeypatch.setattr(
        allocator,
        "get_unavailability_ranges_for_person",
        lambda conn, pid: [(date(2026, 8, 27), date(2026, 8, 27))],
    )

    assert find_candidate() == 1


def test_weekly_cap_blocks_candidate_already_at_limit(monkeypatch):
    monkeypatch.setattr(allocator, "get_position_required_role", lambda conn, pos: "Fighter")
    monkeypatch.setattr(
        allocator,
        "get_available_personnel",
        lambda conn, role: [{"ID": 1, "Full_Name": "A", "Total_Hours_Done": 0}],
    )
    monkeypatch.setattr(allocator, "get_last_shift_end", lambda conn, pid: None)
    monkeypatch.setattr(allocator, "get_unavailability_ranges_for_person", lambda conn, pid: [])
    monkeypatch.setattr(allocator, "get_role_max_shifts_per_week", lambda conn, role: 1)
    monkeypatch.setattr(allocator, "get_weekly_shift_count", lambda conn, pid, start, end: 1)

    assert find_candidate() is None


def test_weekly_cap_allows_candidate_under_limit(monkeypatch):
    monkeypatch.setattr(allocator, "get_position_required_role", lambda conn, pos: "Fighter")
    monkeypatch.setattr(
        allocator,
        "get_available_personnel",
        lambda conn, role: [{"ID": 1, "Full_Name": "A", "Total_Hours_Done": 0}],
    )
    monkeypatch.setattr(allocator, "get_last_shift_end", lambda conn, pid: None)
    monkeypatch.setattr(allocator, "get_unavailability_ranges_for_person", lambda conn, pid: [])
    monkeypatch.setattr(allocator, "get_role_max_shifts_per_week", lambda conn, role: 2)
    monkeypatch.setattr(allocator, "get_weekly_shift_count", lambda conn, pid, start, end: 1)

    assert find_candidate() == 1


def test_role_with_no_cap_is_unlimited(monkeypatch):
    monkeypatch.setattr(allocator, "get_position_required_role", lambda conn, pos: "Fighter")
    monkeypatch.setattr(
        allocator,
        "get_available_personnel",
        lambda conn, role: [{"ID": 1, "Full_Name": "A", "Total_Hours_Done": 0}],
    )
    monkeypatch.setattr(allocator, "get_last_shift_end", lambda conn, pid: None)
    monkeypatch.setattr(allocator, "get_unavailability_ranges_for_person", lambda conn, pid: [])
    monkeypatch.setattr(allocator, "get_role_max_shifts_per_week", lambda conn, role: None)
    monkeypatch.setattr(
        allocator, "get_weekly_shift_count", lambda conn, pid, start, end: 999
    )

    assert find_candidate() == 1


def test_generate_schedule_reports_unresolved_shift_when_no_candidate(monkeypatch):
    patch_defaults(monkeypatch)
    monkeypatch.setattr(allocator, "get_unfilled_shifts", lambda conn: [SAMPLE_SHIFT])
    monkeypatch.setattr(allocator, "get_position_required_role", lambda conn, pos: "Fighter")
    monkeypatch.setattr(allocator, "get_available_personnel", lambda conn, role: [])
    monkeypatch.setattr(allocator, "assign_shift", lambda conn, shift_id, person_id: None)
    monkeypatch.setattr(allocator, "update_total_hours", lambda conn, person_id, hours: None)

    conn = FakeConn()
    result = allocator.generate_schedule(conn)

    assert result["assigned"] == []
    assert result["unresolved"] == [1]
    assert conn.committed is True


def test_generate_schedule_assigns_and_updates_hours_cache(monkeypatch):
    patch_defaults(monkeypatch)
    monkeypatch.setattr(allocator, "get_unfilled_shifts", lambda conn: [SAMPLE_SHIFT])
    monkeypatch.setattr(allocator, "get_position_required_role", lambda conn, pos: "Fighter")
    monkeypatch.setattr(
        allocator,
        "get_available_personnel",
        lambda conn, role: [{"ID": 1, "Full_Name": "A", "Total_Hours_Done": 0}],
    )
    monkeypatch.setattr(allocator, "get_last_shift_end", lambda conn, pid: None)

    recorded_assignments = []
    recorded_hours = []
    monkeypatch.setattr(
        allocator,
        "assign_shift",
        lambda conn, shift_id, person_id: recorded_assignments.append((shift_id, person_id)),
    )
    monkeypatch.setattr(
        allocator,
        "update_total_hours",
        lambda conn, person_id, hours: recorded_hours.append((person_id, hours)),
    )

    conn = FakeConn()
    result = allocator.generate_schedule(conn)

    assert result["assigned"] == [1]
    assert result["unresolved"] == []
    assert recorded_assignments == [(1, 1)]
    assert recorded_hours == [(1, 8.0)]


def test_generate_schedule_enforces_weekly_cap_across_shifts_in_same_run(monkeypatch):
    second_shift = {
        "Shift_ID": 2,
        "Position_Name": "שער ראשי",
        "Date": date(2026, 8, 27),
        "Start_Time": datetime(2026, 8, 27, 6, 0),
        "End_Time": datetime(2026, 8, 27, 14, 0),
    }
    monkeypatch.setattr(allocator, "get_unfilled_shifts", lambda conn: [SAMPLE_SHIFT, second_shift])
    monkeypatch.setattr(allocator, "get_position_required_role", lambda conn, pos: "Fighter")
    monkeypatch.setattr(
        allocator,
        "get_available_personnel",
        lambda conn, role: [{"ID": 1, "Full_Name": "A", "Total_Hours_Done": 0}],
    )
    monkeypatch.setattr(allocator, "get_last_shift_end", lambda conn, pid: None)
    monkeypatch.setattr(allocator, "get_unavailability_ranges_for_person", lambda conn, pid: [])
    monkeypatch.setattr(allocator, "get_role_max_shifts_per_week", lambda conn, role: 1)
    monkeypatch.setattr(allocator, "get_weekly_shift_count", lambda conn, pid, start, end: 0)
    monkeypatch.setattr(allocator, "assign_shift", lambda conn, shift_id, person_id: None)
    monkeypatch.setattr(allocator, "update_total_hours", lambda conn, person_id, hours: None)

    conn = FakeConn()
    result = allocator.generate_schedule(conn)

    assert result["assigned"] == [1]
    assert result["unresolved"] == [2]
