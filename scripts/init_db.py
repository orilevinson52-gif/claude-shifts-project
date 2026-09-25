"""
Database initialization and migration verification script.
Ensures all required tables exist in the database (CREATE TABLE IF NOT EXISTS).
Can be run standalone via CLI or called during application startup.
"""

import argparse
import logging
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mysql.connector
from config import DB_CONFIG, DB_NAME

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("init_db")

# Every data table carries User_ID: each account has its own isolated data.
# Name-keyed tables use (User_ID, name) keys so different users can reuse names.
TABLE_QUERIES = [
    (
        "Users",
        """
        CREATE TABLE IF NOT EXISTS Users (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            Username VARCHAR(50) NOT NULL,
            Password_Hash VARCHAR(255) NOT NULL,
            Created_At DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT uq_users_username UNIQUE (Username)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """,
    ),
    (
        "Roles",
        """
        CREATE TABLE IF NOT EXISTS Roles (
            User_ID INT NOT NULL,
            Role_Name VARCHAR(50) NOT NULL,
            Max_Shifts_Per_Week INT NULL,
            PRIMARY KEY (User_ID, Role_Name),
            CONSTRAINT fk_roles_user
                FOREIGN KEY (User_ID) REFERENCES Users(ID)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """,
    ),
    (
        "Personnel",
        """
        CREATE TABLE IF NOT EXISTS Personnel (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            User_ID INT NOT NULL,
            Full_Name VARCHAR(100) NOT NULL,
            Role VARCHAR(50) NOT NULL,
            Total_Hours_Done DECIMAL(6, 2) NOT NULL DEFAULT 0.00,
            CONSTRAINT fk_personnel_user
                FOREIGN KEY (User_ID) REFERENCES Users(ID),
            CONSTRAINT fk_personnel_role
                FOREIGN KEY (User_ID, Role) REFERENCES Roles(User_ID, Role_Name)
                ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """,
    ),
    (
        "Positions",
        """
        CREATE TABLE IF NOT EXISTS Positions (
            User_ID INT NOT NULL,
            Position_Name VARCHAR(100) NOT NULL,
            Required_Role VARCHAR(50) NOT NULL,
            PRIMARY KEY (User_ID, Position_Name),
            CONSTRAINT fk_positions_user
                FOREIGN KEY (User_ID) REFERENCES Users(ID),
            CONSTRAINT fk_position_role
                FOREIGN KEY (User_ID, Required_Role) REFERENCES Roles(User_ID, Role_Name)
                ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """,
    ),
    (
        "Shifts_Roster",
        """
        CREATE TABLE IF NOT EXISTS Shifts_Roster (
            Shift_ID INT AUTO_INCREMENT PRIMARY KEY,
            User_ID INT NOT NULL,
            Date DATE NOT NULL,
            Start_Time DATETIME NOT NULL,
            End_Time DATETIME NOT NULL,
            Position_Name VARCHAR(100) NOT NULL,
            Assigned_Person_ID INT NULL,
            CONSTRAINT fk_shifts_user
                FOREIGN KEY (User_ID) REFERENCES Users(ID),
            CONSTRAINT fk_shift_position
                FOREIGN KEY (User_ID, Position_Name) REFERENCES Positions(User_ID, Position_Name)
                ON UPDATE CASCADE,
            CONSTRAINT fk_shift_person
                FOREIGN KEY (Assigned_Person_ID) REFERENCES Personnel(ID)
                ON UPDATE CASCADE ON DELETE SET NULL,
            CONSTRAINT chk_shift_times
                CHECK (End_Time > Start_Time)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """,
    ),
    (
        "Personnel_Unavailability",
        """
        CREATE TABLE IF NOT EXISTS Personnel_Unavailability (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            User_ID INT NOT NULL,
            Person_ID INT NOT NULL,
            Start_Date DATE NOT NULL,
            End_Date DATE NOT NULL,
            Reason VARCHAR(200) NULL,
            CONSTRAINT fk_unavailability_user
                FOREIGN KEY (User_ID) REFERENCES Users(ID),
            CONSTRAINT fk_unavailability_person
                FOREIGN KEY (Person_ID) REFERENCES Personnel(ID)
                ON DELETE CASCADE,
            CONSTRAINT chk_unavailability_dates
                CHECK (End_Date >= Start_Date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """,
    ),
]

# Tables from the pre-accounts schema, in safe drop order (children first)
LEGACY_TABLES = ["Personnel_Unavailability", "Shifts_Roster", "Personnel", "Positions", "Roles"]

DEFAULT_ROLES = [
    ("לוחם", None),
    ("מאבטח", None),
    ("סמבצית", 5),
    ("סייר", None),
]


def ensure_database():
    """
    Creates the target database if it doesn't exist yet (e.g. a fresh TiDB
    Cloud Serverless cluster only ships a default 'test' database).
    Connects without selecting a database, since selecting a missing one
    would fail the connection itself.
    """
    cfg = {k: v for k, v in DB_CONFIG.items() if k != "database"}
    conn = mysql.connector.connect(**cfg)
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        cursor.close()
        logger.info("Database '%s' checked/created successfully.", DB_NAME)
    finally:
        conn.close()


def _has_legacy_schema(cursor):
    """True if Roles exists but predates accounts (no User_ID column)."""
    cursor.execute(
        """
        SELECT
            SUM(LOWER(COLUMN_NAME) = 'role_name'),
            SUM(LOWER(COLUMN_NAME) = 'user_id')
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s AND LOWER(TABLE_NAME) = 'roles'
        """,
        (DB_NAME,),
    )
    has_roles, has_user_id = cursor.fetchone()
    return bool(has_roles) and not has_user_id


def migrate_legacy_schema(cursor):
    """
    Replaces the pre-accounts tables with the per-user schema.
    Only runs when the old tables hold nothing but the default roles; if real
    data exists it refuses rather than delete it.
    """
    if not _has_legacy_schema(cursor):
        return

    for table in LEGACY_TABLES[:-1]:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        if count:
            raise RuntimeError(
                f"Legacy table '{table}' has {count} rows; refusing to migrate automatically. "
                "Back up and migrate the data manually."
            )

    logger.info("Legacy schema without accounts detected and empty; recreating tables per user...")
    for table in LEGACY_TABLES:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
        logger.info("Dropped legacy table '%s'.", table)


def ensure_schema(conn=None):
    """
    Verifies that all required tables exist. If missing, creates them.
    Migrates an empty pre-accounts schema to the per-user schema first.
    """
    should_close = False
    if conn is None:
        ensure_database()
        conn = mysql.connector.connect(**DB_CONFIG)
        should_close = True

    try:
        cursor = conn.cursor()

        migrate_legacy_schema(cursor)

        for table_name, query in TABLE_QUERIES:
            cursor.execute(query)
            logger.info("Table '%s' checked/created successfully.", table_name)

        conn.commit()
        cursor.close()
        logger.info("Database schema is ready.")
        return True
    finally:
        if should_close and conn:
            conn.close()


def seed_default_roles(conn, user_id):
    """Gives a new account the standard starting roles. Caller commits."""
    cursor = conn.cursor()
    cursor.executemany(
        "INSERT INTO Roles (User_ID, Role_Name, Max_Shifts_Per_Week) VALUES (%s, %s, %s)",
        [(user_id, name, max_shifts) for name, max_shifts in DEFAULT_ROLES],
    )
    cursor.close()


def seed_sample_data(user_id, conn=None):
    """
    Populates sample personnel and positions for one account if it has none.
    """
    should_close = False
    if conn is None:
        conn = mysql.connector.connect(**DB_CONFIG)
        should_close = True

    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Personnel WHERE User_ID = %s", (user_id,))
        if cursor.fetchone()[0] == 0:
            sample_personnel = [
                ("דניאל כהן", "לוחם"),
                ("יוסי לוי", "לוחם"),
                ("רועי אברהם", "מאבטח"),
                ("מיכל ישראלי", "סמבצית"),
                ("אלון שחר", "סייר"),
            ]
            cursor.executemany(
                "INSERT INTO Personnel (User_ID, Full_Name, Role) VALUES (%s, %s, %s)",
                [(user_id, name, role) for name, role in sample_personnel],
            )
            logger.info("Sample personnel seeded (%d records).", len(sample_personnel))

        cursor.execute("SELECT COUNT(*) FROM Positions WHERE User_ID = %s", (user_id,))
        if cursor.fetchone()[0] == 0:
            sample_positions = [
                ("שער ראשי", "מאבטח"),
                ("חמ\"ל", "סמבצית"),
                ("סיור גדר", "סייר"),
                ("עמדה קדמית", "לוחם"),
            ]
            cursor.executemany(
                "INSERT INTO Positions (User_ID, Position_Name, Required_Role) VALUES (%s, %s, %s)",
                [(user_id, name, role) for name, role in sample_positions],
            )
            logger.info("Sample positions seeded (%d records).", len(sample_positions))

        conn.commit()
        cursor.close()
    finally:
        if should_close and conn:
            conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize Shift Scheduler Database Schema")
    parser.add_argument(
        "--seed-user-id", type=int, help="Seed sample personnel and positions for this user ID"
    )
    args = parser.parse_args()

    logger.info("Connecting to MySQL (%s:%s / %s)...", DB_CONFIG.get("host"), DB_CONFIG.get("port"), DB_CONFIG.get("database"))
    try:
        ensure_schema()
        if args.seed_user_id:
            seed_sample_data(args.seed_user_id)
        print("\n[SUCCESS] מסד הנתונים מוכן ומאומת בהצלחה!")
    except Exception as e:
        logger.error("Database initialization failed: %s", e)
        sys.exit(1)
