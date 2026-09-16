USE shift_scheduler;

ALTER TABLE Roles ADD COLUMN Max_Shifts_Per_Week INT NULL;

CREATE TABLE IF NOT EXISTS Personnel_Unavailability (
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
