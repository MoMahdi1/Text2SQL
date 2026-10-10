
USE employee_ai;

-- =========================================================
-- 1. Create the 40 additional demo employees (11 to 50)
-- =========================================================

DROP TEMPORARY TABLE IF EXISTS seed_employee_names;

CREATE TEMPORARY TABLE seed_employee_names (
    seed_no INT PRIMARY KEY,
    first_name VARCHAR(80) NOT NULL,
    last_name VARCHAR(80) NOT NULL,
    job_title VARCHAR(120) NOT NULL,
    salary DECIMAL(10,2) NOT NULL
);

INSERT INTO seed_employee_names
    (seed_no, first_name, last_name, job_title, salary)
VALUES
    (11, 'Omar', 'Hassan', 'Software Engineer', 18000),
    (12, 'Sara', 'Mahmoud', 'Data Analyst', 15000),
    (13, 'Ahmed', 'Ibrahim', 'Backend Developer', 20000),
    (14, 'Mariam', 'Ali', 'Frontend Developer', 17500),
    (15, 'Youssef', 'Khaled', 'AI Engineer', 25000),
    (16, 'Nour', 'Samir', 'HR Specialist', 12000),
    (17, 'Amr', 'Mostafa', 'DevOps Engineer', 22000),
    (18, 'Salma', 'Adel', 'QA Engineer', 14500),
    (19, 'Karim', 'Tarek', 'Database Administrator', 21000),
    (20, 'Farah', 'Ashraf', 'Product Designer', 16000),
    (21, 'Hassan', 'Fathy', 'Software Engineer', 18500),
    (22, 'Laila', 'Nabil', 'Business Analyst', 15500),
    (23, 'Mahmoud', 'Reda', 'System Administrator', 17000),
    (24, 'Aya', 'Wael', 'Data Scientist', 24000),
    (25, 'Mostafa', 'Ayman', 'Backend Developer', 19500),
    (26, 'Hana', 'Sherif', 'Frontend Developer', 17500),
    (27, 'Ziad', 'Emad', 'AI Engineer', 26000),
    (28, 'Dina', 'Hany', 'Accountant', 13000),
    (29, 'Bassem', 'Gamal', 'Network Engineer', 16500),
    (30, 'Malak', 'Sameh', 'UX Designer', 15500),
    (31, 'Tamer', 'Ehab', 'Software Engineer', 19000),
    (32, 'Reem', 'Fouad', 'Data Analyst', 15000),
    (33, 'Adham', 'Wael', 'Cybersecurity Analyst', 23000),
    (34, 'Jana', 'Hossam', 'QA Engineer', 14500),
    (35, 'Fady', 'Nader', 'DevOps Engineer', 22500),
    (36, 'Menna', 'Ramy', 'HR Specialist', 12500),
    (37, 'Othman', 'Said', 'Backend Developer', 20000),
    (38, 'Nada', 'Magdy', 'Product Designer', 16500),
    (39, 'Eslam', 'Fawzy', 'System Administrator', 17500),
    (40, 'Yara', 'Waheed', 'Data Scientist', 24500),
    (41, 'Khaled', 'Mounir', 'Software Engineer', 18500),
    (42, 'Rana', 'Atef', 'Business Analyst', 15500),
    (43, 'Seif', 'Mohsen', 'AI Engineer', 25500),
    (44, 'Heba', 'Osama', 'Accountant', 13500),
    (45, 'Mina', 'Bishoy', 'Network Engineer', 17000),
    (46, 'Judy', 'Hatem', 'Frontend Developer', 18000),
    (47, 'Bilal', 'Kamel', 'Backend Developer', 20500),
    (48, 'Rita', 'Nabil', 'QA Engineer', 15000),
    (49, 'Sameh', 'Lotfy', 'Database Administrator', 21500),
    (50, 'Farida', 'Essam', 'Data Analyst', 15500);

-- Insert missing employees only.
-- Existing employee records are not overwritten.
INSERT INTO employees (
    first_name,
    last_name,
    email,
    job_title,
    salary,
    hire_date,
    is_active,
    department_id
)
SELECT
    s.first_name,
    s.last_name,
    CONCAT('employee', s.seed_no, '@example.com'),
    s.job_title,
    s.salary,
    DATE_ADD('2020-01-01', INTERVAL MOD(s.seed_no * 17, 2000) DAY),
    TRUE,
    d.department_id
FROM seed_employee_names AS s
JOIN (
    SELECT
        id AS department_id,
        ROW_NUMBER() OVER (ORDER BY id) AS rn,
        COUNT(*) OVER () AS total
    FROM departments
) AS d
    ON d.rn = MOD(s.seed_no - 11, d.total) + 1
WHERE NOT EXISTS (
    SELECT 1
    FROM employees AS e
    WHERE e.email = CONCAT('employee', s.seed_no, '@example.com')
);

-- =========================================================
-- 2. Generate attendance for Sep 1 through Oct 31, 2026
--    Use a temporary table to avoid INSERT/CTE parsing issues.
-- =========================================================

DROP TEMPORARY TABLE IF EXISTS seed_calendar;

CREATE TEMPORARY TABLE seed_calendar (
    work_date DATE PRIMARY KEY
);

INSERT INTO seed_calendar (work_date)
WITH RECURSIVE calendar AS (
    SELECT DATE('2026-09-01') AS work_date

    UNION ALL

    SELECT DATE_ADD(work_date, INTERVAL 1 DAY)
    FROM calendar
    WHERE work_date < DATE('2026-10-31')
)
SELECT work_date
FROM calendar;

-- Generate deterministic attendance times for all employees.
-- Weekends are included intentionally for demo/testing.
-- Generated columns is_late and late_minutes are not inserted.
-- Insert results into a temporary staging table first.

DROP TEMPORARY TABLE IF EXISTS seed_attendance_stage;

CREATE TEMPORARY TABLE seed_attendance_stage (
    employee_id INT UNSIGNED NOT NULL,
    work_date DATE NOT NULL,
    check_in_time TIME NOT NULL,
    check_out_time TIME NULL,
    shift_start_time TIME NOT NULL,
    shift_end_time TIME NOT NULL,
    grace_period_minutes SMALLINT UNSIGNED NOT NULL,
    PRIMARY KEY (employee_id, work_date)
);

INSERT INTO seed_attendance_stage (
    employee_id,
    work_date,
    check_in_time,
    check_out_time,
    shift_start_time,
    shift_end_time,
    grace_period_minutes
)
SELECT
    e.id,
    c.work_date,

    CASE MOD(e.id * 3 + DAYOFYEAR(c.work_date), 10)
        WHEN 0 THEN '08:50:00'
        WHEN 1 THEN '08:58:00'
        WHEN 2 THEN '09:00:00'
        WHEN 3 THEN '09:10:00'
        WHEN 4 THEN '09:14:00'
        WHEN 5 THEN '09:16:00'
        WHEN 6 THEN '09:22:00'
        WHEN 7 THEN '09:35:00'
        WHEN 8 THEN '09:42:00'
        ELSE '10:00:00'
    END,

    CASE
        WHEN MOD(e.id + DAYOFYEAR(c.work_date), 9) = 0
            THEN NULL
        ELSE ADDTIME(
            '17:00:00',
            SEC_TO_TIME(
                MOD(e.id * 5 + DAYOFYEAR(c.work_date), 61) * 60
            )
        )
    END,

    '09:00:00',
    '17:00:00',
    15

FROM employees AS e
CROSS JOIN seed_calendar AS c;

-- Upsert staged records into the real attendance table.
-- The unique key (employee_id, work_date) makes reruns safe.
INSERT INTO attendance_records (
    employee_id,
    work_date,
    check_in_time,
    check_out_time,
    shift_start_time,
    shift_end_time,
    grace_period_minutes
)
SELECT
    employee_id,
    work_date,
    check_in_time,
    check_out_time,
    shift_start_time,
    shift_end_time,
    grace_period_minutes
FROM seed_attendance_stage
ON DUPLICATE KEY UPDATE
    check_in_time = seed_attendance_stage.check_in_time,
    check_out_time = seed_attendance_stage.check_out_time,
    shift_start_time = seed_attendance_stage.shift_start_time,
    shift_end_time = seed_attendance_stage.shift_end_time,
    grace_period_minutes = seed_attendance_stage.grace_period_minutes;

-- Clean up temporary tables.
DROP TEMPORARY TABLE IF EXISTS seed_attendance_stage;
DROP TEMPORARY TABLE IF EXISTS seed_calendar;
DROP TEMPORARY TABLE IF EXISTS seed_employee_names;

-- =========================================================
-- 3. Verification
-- =========================================================

SELECT COUNT(*) AS total_employees
FROM employees;

SELECT
    COUNT(*) AS attendance_records,
    MIN(work_date) AS first_date,
    MAX(work_date) AS last_date,
    SUM(is_late) AS late_records
FROM attendance_records
WHERE work_date BETWEEN '2026-09-01' AND '2026-10-31';

SELECT
    e.id,
    CONCAT(e.first_name, ' ', e.last_name) AS employee_name,
    a.work_date,
    a.check_in_time,
    a.is_late,
    a.late_minutes
FROM attendance_records AS a
JOIN employees AS e ON e.id = a.employee_id
WHERE a.work_date = '2026-10-10'
ORDER BY a.check_in_time;
