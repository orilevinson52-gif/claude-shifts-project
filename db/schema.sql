CREATE DATABASE IF NOT EXISTS shift_scheduler
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE shift_scheduler;

CREATE TABLE Roles (
    Role_Name              VARCHAR(50) PRIMARY KEY,
    Max_Shifts_Per_Week    INT NULL
);

CREATE TABLE Personnel (
    ID                INT AUTO_INCREMENT PRIMARY KEY,
    Full_Name         VARCHAR(100) NOT NULL,
    Role              VARCHAR(50) NOT NULL,
    Total_Hours_Done  DECIMAL(6, 2) NOT NULL DEFAULT 0.00,
    CONSTRAINT fk_personnel_role
        FOREIGN KEY (Role) REFERENCES Roles(Role_Name)
        ON UPDATE CASCADE
);

CREATE TABLE Positions (
    Position_Name    VARCHAR(100) PRIMARY KEY,
    Required_Role    VARCHAR(50) NOT NULL,
    CONSTRAINT fk_position_role
        FOREIGN KEY (Required_Role) REFERENCES Roles(Role_Name)
        ON UPDATE CASCADE
);

CREATE TABLE Shifts_Roster (
    Shift_ID              INT AUTO_INCREMENT PRIMARY KEY,
    Date                  DATE NOT NULL,
    Start_Time            DATETIME NOT NULL,
    End_Time              DATETIME NOT NULL,
    Position_Name         VARCHAR(100) NOT NULL,
    Assigned_Person_ID    INT NULL,
    CONSTRAINT fk_shift_position
        FOREIGN KEY (Position_Name) REFERENCES Positions(Position_Name)
        ON UPDATE CASCADE,
    CONSTRAINT fk_shift_person
        FOREIGN KEY (Assigned_Person_ID) REFERENCES Personnel(ID)
        ON UPDATE CASCADE ON DELETE SET NULL,
    CONSTRAINT chk_shift_times
        CHECK (End_Time > Start_Time)
);

CREATE TABLE Personnel_Unavailability (
    ID            INT AUTO_INCREMENT PRIMARY KEY,
    Person_ID     INT NOT NULL,
    Start_Date    DATE NOT NULL,
    End_Date      DATE NOT NULL,
    Reason        VARCHAR(200) NULL,
    CONSTRAINT fk_unavailability_person
        FOREIGN KEY (Person_ID) REFERENCES Personnel(ID)
        ON DELETE CASCADE,
    CONSTRAINT chk_unavailability_dates
        CHECK (End_Date >= Start_Date)
);
