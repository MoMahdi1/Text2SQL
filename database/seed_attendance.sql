USE employee_ai;

-- Relative dates keep questions such as "Who was late today?" useful whenever
-- the sample data is initialized. Re-running this file on the same day is safe.
INSERT INTO attendance_records
  (
    employee_id,
    work_date,
    check_in_time,
    check_out_time,
    shift_start_time,
    shift_end_time,
    grace_period_minutes
  )
VALUES
  (1, CURDATE(), '08:55:00', '17:05:00', '09:00:00', '17:00:00', 15),
  (2, CURDATE(), '09:10:00', '17:00:00', '09:00:00', '17:00:00', 15),
  (3, CURDATE(), '09:16:00', '17:03:00', '09:00:00', '17:00:00', 15),
  (4, CURDATE(), '09:35:00', NULL,       '09:00:00', '17:00:00', 15),
  (5, CURDATE(), '08:58:00', NULL,       '09:00:00', '17:00:00', 15),
  (6, CURDATE(), '09:00:00', '17:30:00', '09:00:00', '17:00:00', 15),
  (7, DATE_SUB(CURDATE(), INTERVAL 1 DAY), '09:22:00', '17:10:00', '09:00:00', '17:00:00', 15),
  (8, DATE_SUB(CURDATE(), INTERVAL 1 DAY), '08:50:00', '16:55:00', '09:00:00', '17:00:00', 15),
  (1, DATE_SUB(CURDATE(), INTERVAL 2 DAY), '09:18:00', '17:15:00', '09:00:00', '17:00:00', 15),
  (2, DATE_SUB(CURDATE(), INTERVAL 2 DAY), '09:14:00', '17:00:00', '09:00:00', '17:00:00', 15),
  (3, DATE_SUB(CURDATE(), INTERVAL 3 DAY), '09:42:00', NULL,       '09:00:00', '17:00:00', 15),
  (6, DATE_SUB(CURDATE(), INTERVAL 3 DAY), '08:57:00', '17:20:00', '09:00:00', '17:00:00', 15)
ON DUPLICATE KEY UPDATE
  check_in_time = VALUES(check_in_time),
  check_out_time = VALUES(check_out_time),
  shift_start_time = VALUES(shift_start_time),
  shift_end_time = VALUES(shift_end_time),
  grace_period_minutes = VALUES(grace_period_minutes);

