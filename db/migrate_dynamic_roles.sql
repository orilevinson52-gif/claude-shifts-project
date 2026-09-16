USE shift_scheduler;

CREATE TABLE IF NOT EXISTS Roles (
    Role_Name    VARCHAR(50) PRIMARY KEY
);

INSERT IGNORE INTO Roles (Role_Name) VALUES ('Fighter'), ('Commander');

ALTER TABLE Personnel MODIFY Role VARCHAR(50) NOT NULL;
ALTER TABLE Personnel
    ADD CONSTRAINT fk_personnel_role
    FOREIGN KEY (Role) REFERENCES Roles(Role_Name)
    ON UPDATE CASCADE;

ALTER TABLE Positions MODIFY Required_Role VARCHAR(50) NOT NULL;
ALTER TABLE Positions
    ADD CONSTRAINT fk_position_role
    FOREIGN KEY (Required_Role) REFERENCES Roles(Role_Name)
    ON UPDATE CASCADE;
