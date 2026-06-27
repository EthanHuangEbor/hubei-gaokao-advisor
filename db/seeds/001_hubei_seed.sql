INSERT INTO provinces (code, name) VALUES ('HB', '湖北') ON CONFLICT DO NOTHING;
INSERT INTO hubei_subject_types (first_subject, label)
VALUES ('physics', '首选物理'), ('history', '首选历史');

