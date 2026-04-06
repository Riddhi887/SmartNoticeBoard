CREATE DATABASE IF NOT EXISTS smart_notice_board;
USE smart_notice_board;
CREATE TABLE timetable (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  batch        VARCHAR(10)   NOT NULL,
  day_of_week  VARCHAR(10)   NOT NULL,
  start_time   TIME          NOT NULL,
  end_time     TIME          NOT NULL,
  subject_name VARCHAR(50)   NOT NULL,
  subject_code VARCHAR(20),
  teacher_name VARCHAR(60),
  lab_no       INT           DEFAULT 0,
  slot_type    VARCHAR(20)   DEFAULT 'class'
);

INSERT INTO timetable VALUES
-- ===================== MONDAY =====================
(NULL,'TA2','Monday','09:15:00','11:15:00','AQC','AQC101','KK',312,'practical'),
(NULL,'TB2','Monday','11:30:00','13:30:00','AQC','AQC101','DH',312,'practical'),

-- ===================== TUESDAY =====================
(NULL,'TB3','Tuesday','09:15:00','11:15:00','AQC','AQC101','NM',312,'practical'),
(NULL,'D3','Tuesday','11:30:00','13:30:00','PE-II DA','PEII','VD',312,'practical'),

-- ===================== WEDNESDAY =====================
(NULL,'TB1','Wednesday','09:15:00','11:15:00','AQC','AQC101','NM',312,'practical'),
(NULL,'V1','Wednesday','11:30:00','13:30:00','PE-II VCC','PEII','NM',312,'practical'),

-- ===================== THURSDAY =====================
(NULL,'TB4','Thursday','09:15:00','11:15:00','AQC','AQC101','NM',312,'practical'),
(NULL,'TA3','Thursday','02:15:00','16:15:00','AQC','AQC101','KK',312,'practical'),

-- ===================== FRIDAY =====================
(NULL,'V2','Friday','09:15:00','11:15:00','VCC','PEII','NM',312,'practical'),
(NULL,'TA4','Friday','02:15:00','16:15:00','AQC','AQC101','KK',312,'practical'),

-- ===================== SATURDAY =====================
(NULL,'BTech','Saturday','09:15:00','11:15:00','MP&S[H]','MPS101','PG',312,'class'),

-- ===================== BREAKS - ALL DAYS (Mon-Sat) =====================
(NULL,'E312','Monday','08:00:00','09:15:00','Before College','-','-',0,'free'),
(NULL,'E312','Monday','11:15:00','11:30:00','Short Break','-','-',0,'break'),
(NULL,'E312','Monday','13:30:00','14:15:00','Lunch Break','-','-',0,'lunch'),
(NULL,'E312','Monday','16:15:00','23:59:00','No Lab','-','-',0,'free'),

(NULL,'E312','Tuesday','08:00:00','09:15:00','Before College','-','-',0,'free'),
(NULL,'E312','Tuesday','11:15:00','11:30:00','Short Break','-','-',0,'break'),
(NULL,'E312','Tuesday','13:30:00','14:15:00','Lunch Break','-','-',0,'lunch'),
(NULL,'E312','Tuesday','16:15:00','23:59:00','No Lab','-','-',0,'free'),

(NULL,'E312','Wednesday','08:00:00','09:15:00','Before College','-','-',0,'free'),
(NULL,'E312','Wednesday','11:15:00','11:30:00','Short Break','-','-',0,'break'),
(NULL,'E312','Wednesday','13:30:00','14:15:00','Lunch Break','-','-',0,'lunch'),
(NULL,'E312','Wednesday','16:15:00','23:59:00','No Lab','-','-',0,'free'),

(NULL,'E312','Thursday','08:00:00','09:15:00','Before College','-','-',0,'free'),
(NULL,'E312','Thursday','11:15:00','11:30:00','Short Break','-','-',0,'break'),
(NULL,'E312','Thursday','13:30:00','14:15:00','Lunch Break','-','-',0,'lunch'),
(NULL,'E312','Thursday','16:15:00','23:59:00','No Lab','-','-',0,'free'),

(NULL,'E312','Friday','08:00:00','09:15:00','Before College','-','-',0,'free'),
(NULL,'E312','Friday','11:15:00','11:30:00','Short Break','-','-',0,'break'),
(NULL,'E312','Friday','13:30:00','14:15:00','Lunch Break','-','-',0,'lunch'),
(NULL,'E312','Friday','16:15:00','23:59:00','No Lab','-','-',0,'free'),

(NULL,'E312','Saturday','08:00:00','09:15:00','Before College','-','-',0,'free'),
(NULL,'E312','Saturday','11:15:00','11:30:00','Short Break','-','-',0,'break'),
(NULL,'E312','Saturday','13:30:00','23:59:00','No Lab','-','-',0,'free'),

(NULL,'E312','Sunday','00:00:00','23:59:00','No Lab - Weekend','-','-',0,'free');

SELECT * FROM timetable WHERE lab_no = 312 AND slot_type = 'practical';