import mysql.connector

from config import DB_CONFIG


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def get_unfilled_shifts(conn):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT Shift_ID, Date, Start_Time, End_Time, Position_Name
        FROM Shifts_Roster
        WHERE Assigned_Person_ID IS NULL
        ORDER BY Start_Time ASC
        """
    )
    rows = cursor.fetchall()
    cursor.close()
    return rows


def get_position_required_role(conn, position_name):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT Required_Role FROM Positions WHERE Position_Name = %s",
        (position_name,),
    )
    row = cursor.fetchone()
    cursor.close()
    return row["Required_Role"] if row else None


def get_available_personnel(conn, role):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT ID, Full_Name, Total_Hours_Done
        FROM Personnel
        WHERE Role = %s
        """,
        (role,),
    )
    rows = cursor.fetchall()
    cursor.close()
    return rows


def get_last_shift_end(conn, person_id):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT MAX(End_Time) AS last_end
        FROM Shifts_Roster
        WHERE Assigned_Person_ID = %s
        """,
        (person_id,),
    )
    row = cursor.fetchone()
    cursor.close()
    return row["last_end"] if row else None


def assign_shift(conn, shift_id, person_id):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Shifts_Roster SET Assigned_Person_ID = %s WHERE Shift_ID = %s",
        (person_id, shift_id),
    )
    cursor.close()


def update_total_hours(conn, person_id, hours_to_add):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Personnel SET Total_Hours_Done = Total_Hours_Done + %s WHERE ID = %s",
        (hours_to_add, person_id),
    )
    cursor.close()


def clear_all_assignments(conn):
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Shifts_Roster SET Assigned_Person_ID = NULL")
        cursor.execute("UPDATE Personnel SET Total_Hours_Done = 0")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def get_full_roster(conn):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT s.Shift_ID, s.Date, s.Start_Time, s.End_Time, s.Position_Name,
               p.Full_Name AS Assigned_To
        FROM Shifts_Roster s
        LEFT JOIN Personnel p ON s.Assigned_Person_ID = p.ID
        ORDER BY s.Start_Time ASC
        """
    )
    rows = cursor.fetchall()
    cursor.close()
    return rows


def get_hours_summary(conn):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT Full_Name, Total_Hours_Done FROM Personnel ORDER BY Total_Hours_Done DESC"
    )
    rows = cursor.fetchall()
    cursor.close()
    return rows


# --- Roles CRUD ---

def get_all_roles(conn):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT Role_Name, Max_Shifts_Per_Week FROM Roles ORDER BY Role_Name")
    rows = cursor.fetchall()
    cursor.close()
    return rows


def get_role_max_shifts_per_week(conn, role_name):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT Max_Shifts_Per_Week FROM Roles WHERE Role_Name = %s", (role_name,)
    )
    row = cursor.fetchone()
    cursor.close()
    return row["Max_Shifts_Per_Week"] if row else None


def create_role(conn, role_name, max_shifts_per_week=None):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Roles (Role_Name, Max_Shifts_Per_Week) VALUES (%s, %s)",
        (role_name, max_shifts_per_week),
    )
    conn.commit()
    cursor.close()


def update_role(conn, old_role_name, new_role_name, max_shifts_per_week=None):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Roles SET Role_Name = %s, Max_Shifts_Per_Week = %s WHERE Role_Name = %s",
        (new_role_name, max_shifts_per_week, old_role_name),
    )
    conn.commit()
    cursor.close()


def delete_role(conn, role_name):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Roles WHERE Role_Name = %s", (role_name,))
    conn.commit()
    cursor.close()


def delete_all_roles(conn):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Roles")
    conn.commit()
    cursor.close()


# --- Personnel CRUD ---

def get_all_personnel(conn):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT ID, Full_Name, Role, Total_Hours_Done FROM Personnel ORDER BY ID"
    )
    rows = cursor.fetchall()
    cursor.close()
    return rows


def create_person(conn, full_name, role):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Personnel (Full_Name, Role) VALUES (%s, %s)",
        (full_name, role),
    )
    conn.commit()
    cursor.close()


def update_person(conn, person_id, full_name, role):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Personnel SET Full_Name = %s, Role = %s WHERE ID = %s",
        (full_name, role, person_id),
    )
    conn.commit()
    cursor.close()


def delete_person(conn, person_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Personnel WHERE ID = %s", (person_id,))
    conn.commit()
    cursor.close()


def delete_all_personnel(conn):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Personnel")
    conn.commit()
    cursor.close()


# --- Positions CRUD ---

def get_all_positions(conn):
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT Position_Name, Required_Role FROM Positions ORDER BY Position_Name")
    rows = cursor.fetchall()
    cursor.close()
    return rows


def create_position(conn, position_name, required_role):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Positions (Position_Name, Required_Role) VALUES (%s, %s)",
        (position_name, required_role),
    )
    conn.commit()
    cursor.close()


def update_position(conn, old_position_name, new_position_name, required_role):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Positions SET Position_Name = %s, Required_Role = %s WHERE Position_Name = %s",
        (new_position_name, required_role, old_position_name),
    )
    conn.commit()
    cursor.close()


def delete_position(conn, position_name):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Positions WHERE Position_Name = %s", (position_name,))
    conn.commit()
    cursor.close()


def delete_all_positions(conn):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Positions")
    conn.commit()
    cursor.close()


# --- Shifts_Roster CRUD ---

def get_all_shifts(conn):
    return get_full_roster(conn)


def create_shift(conn, date, start_time, end_time, position_name):
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO Shifts_Roster (Date, Start_Time, End_Time, Position_Name)
        VALUES (%s, %s, %s, %s)
        """,
        (date, start_time, end_time, position_name),
    )
    conn.commit()
    cursor.close()


def update_shift(conn, shift_id, date, start_time, end_time, position_name):
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE Shifts_Roster
        SET Date = %s, Start_Time = %s, End_Time = %s, Position_Name = %s
        WHERE Shift_ID = %s
        """,
        (date, start_time, end_time, position_name, shift_id),
    )
    conn.commit()
    cursor.close()


def delete_shift(conn, shift_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Shifts_Roster WHERE Shift_ID = %s", (shift_id,))
    conn.commit()
    cursor.close()


def delete_all_shifts(conn):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Shifts_Roster")
    conn.commit()
    cursor.close()


# --- Personnel_Unavailability CRUD ---

def get_all_unavailability(conn):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT u.ID, u.Person_ID, p.Full_Name, u.Start_Date, u.End_Date, u.Reason
        FROM Personnel_Unavailability u
        JOIN Personnel p ON u.Person_ID = p.ID
        ORDER BY u.Start_Date
        """
    )
    rows = cursor.fetchall()
    cursor.close()
    return rows


def create_unavailability(conn, person_id, start_date, end_date, reason):
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO Personnel_Unavailability (Person_ID, Start_Date, End_Date, Reason)
        VALUES (%s, %s, %s, %s)
        """,
        (person_id, start_date, end_date, reason or None),
    )
    conn.commit()
    cursor.close()


def delete_unavailability(conn, unavailability_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Personnel_Unavailability WHERE ID = %s", (unavailability_id,))
    conn.commit()
    cursor.close()


def delete_all_unavailability(conn):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Personnel_Unavailability")
    conn.commit()
    cursor.close()


def get_unavailability_ranges_for_person(conn, person_id):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT Start_Date, End_Date FROM Personnel_Unavailability WHERE Person_ID = %s",
        (person_id,),
    )
    rows = cursor.fetchall()
    cursor.close()
    return [(row["Start_Date"], row["End_Date"]) for row in rows]


def get_weekly_shift_count(conn, person_id, week_start, week_end):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COUNT(*) FROM Shifts_Roster
        WHERE Assigned_Person_ID = %s AND Date BETWEEN %s AND %s
        """,
        (person_id, week_start, week_end),
    )
    count = cursor.fetchone()[0]
    cursor.close()
    return count
