CREATE DATABASE IF NOT EXISTS employee_ai
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE employee_ai;

CREATE TABLE IF NOT EXISTS departments (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    location VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS employees (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(80) NOT NULL,
    last_name VARCHAR(80) NOT NULL,
    email VARCHAR(160) NOT NULL UNIQUE,
    job_title VARCHAR(120) NOT NULL,
    salary DECIMAL(10, 2) NOT NULL,
    hire_date DATE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    department_id INT UNSIGNED NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_employees_department
      FOREIGN KEY (department_id) REFERENCES departments(id),
    CONSTRAINT chk_salary_positive CHECK (salary > 0)
);

CREATE TABLE IF NOT EXISTS attendance_records (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    employee_id INT UNSIGNED NOT NULL,
    work_date DATE NOT NULL,
    check_in_time TIME NOT NULL,
    check_out_time TIME NULL,
    shift_start_time TIME NOT NULL DEFAULT '09:00:00',
    shift_end_time TIME NOT NULL DEFAULT '17:00:00',
    grace_period_minutes SMALLINT UNSIGNED NOT NULL DEFAULT 15,
    is_late BOOLEAN GENERATED ALWAYS AS (
      TIME_TO_SEC(check_in_time) >
      TIME_TO_SEC(shift_start_time) + (grace_period_minutes * 60)
    ) STORED,
    late_minutes SMALLINT UNSIGNED GENERATED ALWAYS AS (
      GREATEST(
        CEIL(
          (
            TIME_TO_SEC(check_in_time) - TIME_TO_SEC(shift_start_time) -
            (CAST(grace_period_minutes AS SIGNED) * 60)
          ) / 60
        ),
        0
      )
    ) STORED,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_attendance_employee
      FOREIGN KEY (employee_id) REFERENCES employees(id),
    CONSTRAINT uq_attendance_employee_work_date
      UNIQUE (employee_id, work_date),
    CONSTRAINT chk_attendance_shift_order
      CHECK (shift_end_time > shift_start_time),
    CONSTRAINT chk_attendance_grace_period
      CHECK (grace_period_minutes <= 180),
    CONSTRAINT chk_attendance_checkout
      CHECK (check_out_time IS NULL OR check_out_time >= check_in_time),
    INDEX idx_attendance_work_date (work_date),
    INDEX idx_attendance_late_date (is_late, work_date)
);

CREATE USER IF NOT EXISTS 'readonly_user'@'%' IDENTIFIED BY 'readonly_password';
GRANT SELECT ON employee_ai.* TO 'readonly_user'@'%';
FLUSH PRIVILEGES;
