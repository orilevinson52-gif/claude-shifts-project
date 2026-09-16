USE shift_scheduler;

INSERT INTO Roles (Role_Name) VALUES
    ('Fighter'),
    ('Commander');

INSERT INTO Personnel (Full_Name, Role, Total_Hours_Done) VALUES
    ('דני כהן',      'Fighter',   0),
    ('מיכל לוי',     'Fighter',   0),
    ('יוסי אברהם',   'Fighter',   0),
    ('נועה שמעוני',  'Fighter',   0),
    ('רון פרץ',      'Commander', 0),
    ('שירה גולן',    'Commander', 0);

INSERT INTO Positions (Position_Name, Required_Role) VALUES
    ('שער ראשי',   'Fighter'),
    ('סיור היקפי', 'Fighter'),
    ('חמ"ל',       'Commander');

INSERT INTO Shifts_Roster (Date, Start_Time, End_Time, Position_Name, Assigned_Person_ID) VALUES
    ('2026-08-26', '2026-08-26 06:00:00', '2026-08-26 14:00:00', 'שער ראשי',   NULL),
    ('2026-08-26', '2026-08-26 14:00:00', '2026-08-26 22:00:00', 'שער ראשי',   NULL),
    ('2026-08-26', '2026-08-26 22:00:00', '2026-08-27 06:00:00', 'שער ראשי',   NULL),
    ('2026-08-26', '2026-08-26 06:00:00', '2026-08-26 14:00:00', 'סיור היקפי', NULL),
    ('2026-08-26', '2026-08-26 14:00:00', '2026-08-26 22:00:00', 'סיור היקפי', NULL),
    ('2026-08-26', '2026-08-26 06:00:00', '2026-08-26 18:00:00', 'חמ"ל',       NULL),
    ('2026-08-27', '2026-08-27 06:00:00', '2026-08-27 14:00:00', 'שער ראשי',   NULL),
    ('2026-08-27', '2026-08-27 14:00:00', '2026-08-27 22:00:00', 'שער ראשי',   NULL),
    ('2026-08-27', '2026-08-27 06:00:00', '2026-08-27 18:00:00', 'חמ"ל',       NULL);
