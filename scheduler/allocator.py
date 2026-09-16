from datetime import timedelta

from config import MIN_REST_HOURS
from db.connection import (
    assign_shift,
    get_available_personnel,
    get_last_shift_end,
    get_position_required_role,
    get_role_max_shifts_per_week,
    get_unavailability_ranges_for_person,
    get_unfilled_shifts,
    get_weekly_shift_count,
    update_total_hours,
)


def shift_duration_hours(shift):
    return round((shift["End_Time"] - shift["Start_Time"]).total_seconds() / 3600, 2)


def week_bounds(day):
    days_since_sunday = (day.weekday() + 1) % 7
    week_start = day - timedelta(days=days_since_sunday)
    week_end = week_start + timedelta(days=6)
    return week_start, week_end


def is_unavailable(shift_date, ranges):
    return any(start <= shift_date <= end for start, end in ranges)


def find_best_candidate(
    conn,
    shift,
    last_shift_end_cache,
    hours_done_cache,
    unavailability_cache,
    role_max_cache,
    weekly_count_cache,
):
    role = get_position_required_role(conn, shift["Position_Name"])
    if role is None:
        return None

    if role not in role_max_cache:
        role_max_cache[role] = get_role_max_shifts_per_week(conn, role)
    role_max = role_max_cache[role]

    week_start, week_end = week_bounds(shift["Date"])

    candidates = get_available_personnel(conn, role)
    valid_candidates = []

    for person in candidates:
        person_id = person["ID"]

        if person_id not in last_shift_end_cache:
            last_shift_end_cache[person_id] = get_last_shift_end(conn, person_id)
        last_end = last_shift_end_cache[person_id]

        if last_end is not None:
            rest_hours = (shift["Start_Time"] - last_end).total_seconds() / 3600
            if rest_hours < MIN_REST_HOURS:
                continue

        if person_id not in unavailability_cache:
            unavailability_cache[person_id] = get_unavailability_ranges_for_person(conn, person_id)
        if is_unavailable(shift["Date"], unavailability_cache[person_id]):
            continue

        if role_max is not None:
            week_key = (person_id, week_start)
            if week_key not in weekly_count_cache:
                weekly_count_cache[week_key] = get_weekly_shift_count(conn, person_id, week_start, week_end)
            if weekly_count_cache[week_key] >= role_max:
                continue

        if person_id not in hours_done_cache:
            hours_done_cache[person_id] = float(person["Total_Hours_Done"])

        valid_candidates.append((person_id, hours_done_cache[person_id]))

    if not valid_candidates:
        return None

    valid_candidates.sort(key=lambda candidate: candidate[1])
    return valid_candidates[0][0]


def generate_schedule(conn):
    shifts = get_unfilled_shifts(conn)

    last_shift_end_cache = {}
    hours_done_cache = {}
    unavailability_cache = {}
    role_max_cache = {}
    weekly_count_cache = {}
    assigned_shift_ids = []
    unresolved_shift_ids = []

    try:
        for shift in shifts:
            chosen_person_id = find_best_candidate(
                conn,
                shift,
                last_shift_end_cache,
                hours_done_cache,
                unavailability_cache,
                role_max_cache,
                weekly_count_cache,
            )

            if chosen_person_id is None:
                unresolved_shift_ids.append(shift["Shift_ID"])
                continue

            duration = shift_duration_hours(shift)

            assign_shift(conn, shift["Shift_ID"], chosen_person_id)
            update_total_hours(conn, chosen_person_id, duration)

            hours_done_cache[chosen_person_id] += duration
            last_shift_end_cache[chosen_person_id] = shift["End_Time"]

            week_start, _ = week_bounds(shift["Date"])
            week_key = (chosen_person_id, week_start)
            weekly_count_cache[week_key] = weekly_count_cache.get(week_key, 0) + 1

            assigned_shift_ids.append(shift["Shift_ID"])

        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return {
        "assigned": assigned_shift_ids,
        "unresolved": unresolved_shift_ids,
    }
