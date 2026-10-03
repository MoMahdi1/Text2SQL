USE employee_ai;

INSERT INTO departments (id, name, location) VALUES
  (1, 'Engineering', 'Cairo'),
  (2, 'Human Resources', 'Giza'),
  (3, 'Sales', 'Alexandria'),
  (4, 'Finance', 'Cairo')
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  location = VALUES(location);

INSERT INTO employees
  (id, first_name, last_name, email, job_title, salary, hire_date, is_active, department_id)
VALUES
  (1, 'Omar', 'Hassan', 'omar.hassan@example.com', 'Backend Developer', 24000.00, '2023-02-12', TRUE, 1),
  (2, 'Mariam', 'Ali', 'mariam.ali@example.com', 'Frontend Developer', 22000.00, '2023-07-03', TRUE, 1),
  (3, 'Youssef', 'Ibrahim', 'youssef.ibrahim@example.com', 'QA Engineer', 19000.00, '2024-01-15', TRUE, 1),
  (4, 'Nour', 'Mostafa', 'nour.mostafa@example.com', 'HR Specialist', 17500.00, '2022-11-20', TRUE, 2),
  (5, 'Ahmed', 'Samir', 'ahmed.samir@example.com', 'Recruiter', 16500.00, '2024-05-08', TRUE, 2),
  (6, 'Salma', 'Mahmoud', 'salma.mahmoud@example.com', 'Sales Manager', 28000.00, '2021-09-01', TRUE, 3),
  (7, 'Karim', 'Adel', 'karim.adel@example.com', 'Sales Representative', 15500.00, '2024-03-11', TRUE, 3),
  (8, 'Dina', 'Fathy', 'dina.fathy@example.com', 'Accountant', 20500.00, '2022-06-17', TRUE, 4),
  (9, 'Hany', 'Kamal', 'hany.kamal@example.com', 'Financial Analyst', 23000.00, '2023-10-23', FALSE, 4),
  (10, 'Laila', 'Tarek', 'laila.tarek@example.com', 'Engineering Manager', 35000.00, '2020-04-05', TRUE, 1)
ON DUPLICATE KEY UPDATE
  first_name = VALUES(first_name),
  last_name = VALUES(last_name),
  email = VALUES(email),
  job_title = VALUES(job_title),
  salary = VALUES(salary),
  hire_date = VALUES(hire_date),
  is_active = VALUES(is_active),
  department_id = VALUES(department_id);

