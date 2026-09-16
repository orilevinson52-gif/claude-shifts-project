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

TABLE_QUERIES = [
    (
        "Roles",
        """
        CREATE TABLE IF NOT EXISTS Roles (
            Role_Name VARCHAR(50) PRIMARY KEY,
            Max_Shifts_Per_Week INT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """,
    ),
    (
        "Personnel",
        """
        CREATE TABLE IF NOT EXISTS Personnel (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            Full_Name VARCHAR(100) NOT NULL,
            Role VARCHAR(50) NOT NULL,
            Total_Hours_Done DECIMAL(6, 2) NOT NULL DEFAULT 0.00,
            CONSTRAINT fk_personnel_role
                FOREIGN KEY (Role) REFERENCES Roles(Role_Name)
                ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """,
    ),
    (
        "Positions",
        """
        CREATE TABLE IF NOT EXISTS Positions (
            Position_Name VARCHAR(100) PRIMARY KEY,
            Required_Role VARCHAR(50) NOT NULL,
            CONSTRAINT fk_position_role
                FOREIGN KEY (Required_Role) REFERENCES Roles(Role_Name)
                ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """,
    ),
    (
        "Shifts_Roster",
        """
        CREATE TABLE IF NOT EXISTS Shifts_Roster (
            Shift_ID INT AUTO_INCREMENT PRIMARY KEY,
            Date DATE NOT NULL,
            Start_Time DATETIME NOT NULL,
            End_Time DATETIME NOT NULL,
            Position_Name VARCHAR(100) NOT NULL,
            Assigned_Person_ID INT NULL,
            CONSTRAINT fk_shift_position
                FOREIGN KEY (Position_Name) REFERENCES Positions(Position_Name)
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
            Person_ID INT NOT NULL,
            Start_Date DATE NOT NULL,
            End_Date DATE NOT NULL,
            Reason VARCHAR(200) NULL,
            CONSTRAINT fk_unavailability_person
                FOREIGN KEY (Person_ID) REFERENCES Personnel(ID)
                ON DELETE CASCADE,
            CONSTRAINT chk_unavailability_dates
                CHECK (End_Date >= Start_Date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """,
    ),
]

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


def ensure_schema(conn=None):
    """
    Verifies that all required tables exist. If missing, creates them.
    Also ensures basic default roles exist if the Roles table is empty.
    """
    should_close = False
    if conn is None:
        ensure_database()
        conn = mysql.connector.connect(**DB_CONFIG)
        should_close = True

    try:
        cursor = conn.cursor()

        # 1. Create tables
        for table_name, query in TABLE_QUERIES:
            cursor.execute(query)
            logger.info("Table '%s' checked/created successfully.", table_name)

        # 2. Seed basic roles if Roles table is completely empty
        cursor.execute("SELECT COUNT(*) FROM Roles")
        roles_count = cursor.fetchone()[0]
        if roles_count == 0:
            logger.info("Seeding initial default roles...")
            cursor.executemany(
                "INSERT INTO Roles (Role_Name, Max_Shifts_Per_Week) VALUES (%s, %s)",
                DEFAULT_ROLES,
            )
            conn.commit()
            logger.info("Default roles created: %s", [r[0] for r in DEFAULT_ROLES])

        cursor.close()
        logger.info("Database schema is ready.")
        return True
    finally:
        if should_close and conn:
            conn.close()


def seed_sample_data(conn=None):
    """
    Populates sample personnel and positions if requested.
    """
    should_close = False
    if conn is None:
        conn = mysql.connector.connect(**DB_CONFIG)
        should_close = True

    try:
        cursor = conn.cursor()

        # Seed sample personnel if empty
        cursor.execute("SELECT COUNT(*) FROM Personnel")
        if cursor.fetchone()[0] == 0:
            sample_personnel = [
                ("דניאל כהן", "לוחם"),
                ("יוסי לוי", "לוחם"),
                ("רועי אברהם", "מאבטח"),
                ("מיכל ישראלי", "סמבצית"),
                ("אלון שחר", "סייר"),
            ]
            cursor.executemany(
                "INSERT INTO Personnel (Full_Name, Role) VALUES (%s, %s)",
                sample_personnel,
            )
            logger.info("Sample personnel seeded (%d records).", len(sample_personnel))

        # Seed sample positions if empty
        cursor.execute("SELECT COUNT(*) FROM Positions")
        if cursor.fetchone()[0] == 0:
            sample_positions = [
                ("שער ראשי", "מאבטח"),
                ("חמ\"ל", "סמבצית"),
                ("סיור גדר", "סייר"),
                ("עמדה קדמית", "לוחם"),
            ]
            cursor.executemany(
                "INSERT INTO Positions (Position_Name, Required_Role) VALUES (%s, %s)",
                sample_positions,
            )
            logger.info("Sample positions seeded (%d records).", len(sample_positions))

        conn.commit()
        cursor.close()
    finally:
        if should_close and conn:
            conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize Shift Scheduler Database Schema")
    parser.add_argument("--seed", action="store_true", help="Seed sample personnel and positions")
    args = parser.parse_args()

    logger.info("Connecting to MySQL (%s:%s / %s)...", DB_CONFIG.get("host"), DB_CONFIG.get("port"), DB_CONFIG.get("database"))
    try:
        ensure_schema()
        if args.seed:
            seed_sample_data()
        print("\n[SUCCESS] מסד הנתונים מוכן ומאומת בהצלחה!")
    except Exception as e:
        logger.error("Database initialization failed: %s", e)
        sys.exit(1)
