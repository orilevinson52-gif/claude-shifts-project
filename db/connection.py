import mysql.connector

from config import DB_CONFIG


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


# --- Users ---

def create_user(conn, username, password_hash):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Users (Username, Password_Hash) VALUES (%s, %s)",
        (username, password_hash),
    )
    user_id = cursor.lastrowid
    cursor.close()
    return user_id


def get_user_by_username(conn, username):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT ID, Username, Password_Hash FROM Users WHERE Username = %s",
        (username,),
    )
    row = cursor.fetchone()
    cursor.close()
    return row


# --- Scheduler queries ---

def get_unfilled_shifts(conn, user_id):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT Shift_ID, Date, Start_Time, End_Time, Position_Name
        FROM Shifts_Roster
        WHERE User_ID = %s AND Assigned_Person_ID IS NULL
        ORDER BY Start_Time ASC
        """,
        (user_id,),
    )
    rows = cursor.fetchall()
    cursor.close()
    return rows


def get_position_required_role(conn, user_id, position_name):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT Required_Role FROM Positions WHERE User_ID = %s AND Position_Name = %s",
        (user_id, position_name),
    )
    row = cursor.fetchone()
    cursor.close()
    return row["Required_Role"] if row else None


def get_available_personnel(conn, user_id, role):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT ID, Full_Name, Total_Hours_Done
        FROM Personnel
        WHERE User_ID = %s AND Role = %s
        """,
        (user_id, role),
    )
    rows = cursor.fetchall()
    cursor.close()
    return rows


def get_last_shift_end(conn, user_id, person_id):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT MAX(End_Time) AS last_end
        FROM Shifts_Roster
        WHERE User_ID = %s AND Assigned_Person_ID = %s
        """,
        (user_id, person_id),
    )
    row = cursor.fetchone()
    cursor.close()
    return row["last_end"] if row else None


def assign_shift(conn, user_id, shift_id, person_id):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Shifts_Roster SET Assigned_Person_ID = %s WHERE User_ID = %s AND Shift_ID = %s",
        (person_id, user_id, shift_id),
    )
    cursor.close()


def update_total_hours(conn, user_id, person_id, hours_to_add):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Personnel SET Total_Hours_Done = Total_Hours_Done + %s WHERE User_ID = %s AND ID = %s",
        (hours_to_add, user_id, person_id),
    )
    cursor.close()


def clear_all_assignments(conn, user_id):
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Shifts_Roster SET Assigned_Person_ID = NULL WHERE User_ID = %s", (user_id,))
        cursor.execute("UPDATE Personnel SET Total_Hours_Done = 0 WHERE User_ID = %s", (user_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def get_full_roster(conn, user_id):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT s.Shift_ID, s.Date, s.Start_Time, s.End_Time, s.Position_Name,
               p.Full_Name AS Assigned_To
        FROM Shifts_Roster s
        LEFT JOIN Personnel p ON s.Assigned_Person_ID = p.ID AND p.User_ID = s.User_ID
        WHERE s.User_ID = %s
        ORDER BY s.Start_Time ASC
        """,
        (user_id,),
    )
    rows = cursor.fetchall()
    cursor.close()
    return rows


def get_hours_summary(conn, user_id):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT Full_Name, Total_Hours_Done FROM Personnel
        WHERE User_ID = %s
        ORDER BY Total_Hours_Done DESC
        """,
        (user_id,),
    )
    rows = cursor.fetchall()
    cursor.close()
    return rows


# --- Roles CRUD ---

def get_all_roles(conn, user_id):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT Role_Name, Max_Shifts_Per_Week FROM Roles WHERE User_ID = %s ORDER BY Role_Name",
        (user_id,),
    )
    rows = cursor.fetchall()
    cursor.close()
    return rows


def get_role_max_shifts_per_week(conn, user_id, role_name):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT Max_Shifts_Per_Week FROM Roles WHERE User_ID = %s AND Role_Name = %s",
        (user_id, role_name),
    )
    row = cursor.fetchone()
    cursor.close()
    return row["Max_Shifts_Per_Week"] if row else None


def create_role(conn, user_id, role_name, max_shifts_per_week=None):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Roles (User_ID, Role_Name, Max_Shifts_Per_Week) VALUES (%s, %s, %s)",
        (user_id, role_name, max_shifts_per_week),
    )
    conn.commit()
    cursor.close()


def update_role(conn, user_id, old_role_name, new_role_name, max_shifts_per_week=None):
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE Roles SET Role_Name = %s, Max_Shifts_Per_Week = %s
        WHERE User_ID = %s AND Role_Name = %s
        """,
        (new_role_name, max_shifts_per_week, user_id, old_role_name),
    )
    conn.commit()
    cursor.close()


def delete_role(conn, user_id, role_name):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Roles WHERE User_ID = %s AND Role_Name = %s", (user_id, role_name))
    conn.commit()
    cursor.close()


def delete_all_roles(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Roles WHERE User_ID = %s", (user_id,))
    conn.commit()
    cursor.close()


# --- Personnel CRUD ---

def get_all_personnel(conn, user_id):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT ID, Full_Name, Role, Total_Hours_Done FROM Personnel WHERE User_ID = %s ORDER BY ID",
        (user_id,),
    )
    rows = cursor.fetchall()
    cursor.close()
    return rows


def create_person(conn, user_id, full_name, role):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Personnel (User_ID, Full_Name, Role) VALUES (%s, %s, %s)",
        (user_id, full_name, role),
    )
    conn.commit()
    cursor.close()


def update_person(conn, user_id, person_id, full_name, role):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Personnel SET Full_Name = %s, Role = %s WHERE User_ID = %s AND ID = %s",
        (full_name, role, user_id, person_id),
    )
    conn.commit()
    cursor.close()


def delete_person(conn, user_id, person_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Personnel WHERE User_ID = %s AND ID = %s", (user_id, person_id))
    conn.commit()
    cursor.close()


def delete_all_personnel(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Personnel WHERE User_ID = %s", (user_id,))
    conn.commit()
    cursor.close()


# --- Positions CRUD ---

def get_all_positions(conn, user_id):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT Position_Name, Required_Role FROM Positions WHERE User_ID = %s ORDER BY Position_Name",
        (user_id,),
    )
    rows = cursor.fetchall()
    cursor.close()
    return rows


def create_position(conn, user_id, position_name, required_role):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Positions (User_ID, Position_Name, Required_Role) VALUES (%s, %s, %s)",
        (user_id, position_name, required_role),
    )
    conn.commit()
    cursor.close()


def update_position(conn, user_id, old_position_name, new_position_name, required_role):
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE Positions SET Position_Name = %s, Required_Role = %s
        WHERE User_ID = %s AND Position_Name = %s
        """,
        (new_position_name, required_role, user_id, old_position_name),
    )
    conn.commit()
    cursor.close()


def delete_position(conn, user_id, position_name):
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM Positions WHERE User_ID = %s AND Position_Name = %s", (user_id, position_name)
    )
    conn.commit()
    cursor.close()


def delete_all_positions(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Positions WHERE User_ID = %s", (user_id,))
    conn.commit()
    cursor.close()


# --- Shifts_Roster CRUD ---

def get_all_shifts(conn, user_id):
    return get_full_roster(conn, user_id)


def create_shift(conn, user_id, date, start_time, end_time, position_name):
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO Shifts_Roster (User_ID, Date, Start_Time, End_Time, Position_Name)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (user_id, date, start_time, end_time, position_name),
    )
    conn.commit()
    cursor.close()


def update_shift(conn, user_id, shift_id, date, start_time, end_time, position_name):
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE Shifts_Roster
        SET Date = %s, Start_Time = %s, End_Time = %s, Position_Name = %s
        WHERE User_ID = %s AND Shift_ID = %s
        """,
        (date, start_time, end_time, position_name, user_id, shift_id),
    )
    conn.commit()
    cursor.close()


def delete_shift(conn, user_id, shift_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Shifts_Roster WHERE User_ID = %s AND Shift_ID = %s", (user_id, shift_id))
    conn.commit()
    cursor.close()


def delete_all_shifts(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Shifts_Roster WHERE User_ID = %s", (user_id,))
    conn.commit()
    cursor.close()


# --- Personnel_Unavailability CRUD ---

def get_all_unavailability(conn, user_id):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT u.ID, u.Person_ID, p.Full_Name, u.Start_Date, u.End_Date, u.Reason
        FROM Personnel_Unavailability u
        JOIN Personnel p ON u.Person_ID = p.ID AND p.User_ID = u.User_ID
        WHERE u.User_ID = %s
        ORDER BY u.Start_Date
        """,
        (user_id,),
    )
    rows = cursor.fetchall()
    cursor.close()
    return rows


def create_unavailability(conn, user_id, person_id, start_date, end_date, reason):
    # INSERT ... SELECT so a person_id belonging to another user inserts nothing
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO Personnel_Unavailability (User_ID, Person_ID, Start_Date, End_Date, Reason)
        SELECT User_ID, ID, %s, %s, %s FROM Personnel WHERE User_ID = %s AND ID = %s
        """,
        (start_date, end_date, reason or None, user_id, person_id),
    )
    conn.commit()
    cursor.close()


def delete_unavailability(conn, user_id, unavailability_id):
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM Personnel_Unavailability WHERE User_ID = %s AND ID = %s",
        (user_id, unavailability_id),
    )
    conn.commit()
    cursor.close()


def delete_all_unavailability(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Personnel_Unavailability WHERE User_ID = %s", (user_id,))
    conn.commit()
    cursor.close()


def get_unavailability_ranges_for_person(conn, user_id, person_id):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT Start_Date, End_Date FROM Personnel_Unavailability
        WHERE User_ID = %s AND Person_ID = %s
        """,
        (user_id, person_id),
    )
    rows = cursor.fetchall()
    cursor.close()
    return [(row["Start_Date"], row["End_Date"]) for row in rows]


def get_weekly_shift_count(conn, user_id, person_id, week_start, week_end):
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT COUNT(*) FROM Shifts_Roster
        WHERE User_ID = %s AND Assigned_Person_ID = %s AND Date BETWEEN %s AND %s
        """,
        (user_id, person_id, week_start, week_end),
    )
    count = cursor.fetchone()[0]
    cursor.close()
    return count
