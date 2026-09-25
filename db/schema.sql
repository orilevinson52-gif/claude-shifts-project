CREATE DATABASE IF NOT EXISTS shift_scheduler
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE shift_scheduler;

-- Generated from scripts/init_db.py TABLE_QUERIES (the source of truth).
-- Every data table is scoped by User_ID: each account has its own isolated data.

CREATE TABLE IF NOT EXISTS Users (
    ID INT AUTO_INCREMENT PRIMARY KEY,
    Username VARCHAR(50) NOT NULL,
    Password_Hash VARCHAR(255) NOT NULL,
    Created_At DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_users_username UNIQUE (Username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS Roles (
    User_ID INT NOT NULL,
    Role_Name VARCHAR(50) NOT NULL,
    Max_Shifts_Per_Week INT NULL,
    PRIMARY KEY (User_ID, Role_Name),
    CONSTRAINT fk_roles_user
        FOREIGN KEY (User_ID) REFERENCES Users(ID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

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
