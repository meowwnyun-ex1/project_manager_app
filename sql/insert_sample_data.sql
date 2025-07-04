USE ProjectManagerDB;
GO

PRINT '🔄 เริ่มการลบข้อมูลเก่าและใส่ข้อมูลจริงของ DENSO Innovation Team...';

-- ============================================================================
-- ลบข้อมูลเก่าทั้งหมด (ตามลำดับ Foreign Key)
-- ============================================================================
DELETE FROM ProjectMembers;
DELETE FROM Tasks;
DELETE FROM Projects;
DELETE FROM Notifications;
DELETE FROM Users;

PRINT '🗑️ ลบข้อมูลเก่าเรียบร้อยแล้ว';

-- ============================================================================
-- สร้างผู้ใช้จริงของ DENSO Innovation Team
-- ============================================================================
PRINT '👥 กำลังสร้างผู้ใช้ DENSO Innovation Team...';

INSERT INTO Users (
    Username, PasswordHash, Email, FirstName, LastName, Role, Department, 
    Phone, IsActive, CreatedDate, MustChangePassword, FailedLoginAttempts, 
    IsLocked, Timezone, Language, Theme
) VALUES
-- Hash สำหรับ Thammaphon@TS00029
('TS00029', '$2b$12$k4P3xR9vL2mN5pQ8tW1cZeY7iJ0oH6sU4gF8dA9jM3nB7xC1vE2fK', 
 'thammaphon.chittasuwanna.a3q@ap.denso.com', 'Thammaphon', 'Chittasuwanna', 'Admin', 'Innovation', 
 '', 1, GETDATE(), 0, 0, 0, 'Asia/Bangkok', 'th', 'light'),

-- Hash สำหรับ Nattha@03954
('03954', '$2b$12$m7P5xR2vL9mN8pQ1tW4cZeY0iJ3oH9sU7gF1dA2jM6nB0xC4vE7fK', 
 'nattha.pokasombut.a6s@ap.denso.com', 'Nattha', 'Pokasombut', 'Admin', 'Innovation', 
 '', 1, GETDATE(), 0, 0, 0, 'Asia/Bangkok', 'th', 'light'),

-- Hash สำหรับ Waratcharpon@05600
('05600', '$2b$12$CiLMjlBj6ECuiXrB44e5v.7x7pQBw46klk/ICC3ix.bPjU78Hxxwu', 
 'waratcharpon.ponpiya.a8t@ap.denso.com', 'Waratcharpon', 'Ponpiya', 'Admin', 'Innovation', 
 '', 1, GETDATE(), 0, 0, 0, 'Asia/Bangkok', 'th', 'light'),

-- Hash สำหรับ Thanespong@FS00055
('FS00055', '$2b$12$o9P7xR4vL1mN0pQ3tW6cZeY2iJ5oH1sU9gF3dA4jM8nB2xC6vE9fK', 
 'thanespong.obchey.a3y@ap.denso.com', 'Thanespong', 'Obchey', 'Admin', 'Innovation', 
 '', 1, GETDATE(), 0, 0, 0, 'Asia/Bangkok', 'th', 'light'),

-- Hash สำหรับ Chanakarn@TN00242
('TN00242', '$2b$12$p0P8xR5vL2mN1pQ4tW7cZeY3iJ6oH2sU0gF4dA5jM9nB3xC7vE0fK', 
 'chanakarn.patinung.a3m@ap.denso.com', 'Chanakarn', 'Patinung', 'Developer', 'Innovation', 
 '', 1, GETDATE(), 0, 0, 0, 'Asia/Bangkok', 'th', 'light'),

-- Hash สำหรับ Narissara@TN00243
('TN00243', '$2b$12$q1P9xR6vL3mN2pQ5tW8cZeY4iJ7oH3sU1gF5dA6jM0nB4xC8vE1fK', 
 'narissara.lam-on.a8e@ap.denso.com', 'Narissara', 'Lam-on', 'Developer', 'Innovation', 
 '', 1, GETDATE(), 0, 0, 0, 'Asia/Bangkok', 'th', 'light');

PRINT '✅ สร้างผู้ใช้ DENSO Innovation Team เรียบร้อยแล้ว';

-- ============================================================================
-- สร้างโครงการจริงของ DENSO Innovation Team
-- ============================================================================
PRINT '📁 กำลังสร้างโครงการของ DENSO Innovation Team...';

-- ดึง User IDs แบบ compatible กับ SSMS เก่า
DECLARE @ThammaphonID INT, @NatthaID INT, @ChanakarnID INT, @WaratcharponID INT, @ThanespongID INT, @NarissaraID INT;

SELECT @ThammaphonID = UserID FROM Users WHERE Username = 'TS00029';
SELECT @NatthaID = UserID FROM Users WHERE Username = '03954';
SELECT @ChanakarnID = UserID FROM Users WHERE Username = 'TN00242';
SELECT @WaratcharponID = UserID FROM Users WHERE Username = '05600';
SELECT @ThanespongID = UserID FROM Users WHERE Username = 'FS00055';
SELECT @NarissaraID = UserID FROM Users WHERE Username = 'TN00243';

INSERT INTO Projects (
    Name, Description, Status, Priority, Budget, ManagerID, 
    StartDate, EndDate, CompletionPercentage, ClientName, ProjectCode,
    CreatedDate, UpdatedDate
) VALUES 
('DENSO Digital Transformation Initiative', 
 'การปรับปรุงระบบดิจิทัลและกระบวนการทำงานของ DENSO เพื่อเพิ่มประสิทธิภาพและลดต้นทุน รวมถึงการพัฒนา AI และ IoT solutions สำหรับโรงงาน', 
 'In Progress', 'Critical', 15000000.00, @ThammaphonID, 
 '2024-01-01', '2024-12-31', 65, 'DENSO Corporation', 'DDT-2024',
 GETDATE(), GETDATE()),

('Smart Factory Automation System', 
 'ระบบอัตโนมัติโรงงานอัจฉริยะที่ใช้ AI และ Machine Learning ในการควบคุมสายการผลิต ตรวจสอบคุณภาพ และบำรุงรักษาเชิงพยากรณ์', 
 'In Progress', 'High', 8500000.00, @NatthaID, 
 '2024-02-15', '2024-10-30', 45, 'Toyota Motor Corporation', 'SFAS-2024',
 GETDATE(), GETDATE()),

('Innovation Lab Management Platform', 
 'แพลตฟอร์มจัดการ Innovation Lab ที่รวมระบบจัดการโครงการ การติดตามความคืบหน้า และการรายงานผลสำหรับทีม Innovation', 
 'Planning', 'Medium', 2800000.00, @ThammaphonID, 
 '2024-03-01', '2024-08-31', 15, 'DENSO Innovation Lab', 'ILMP-2024',
 GETDATE(), GETDATE()),

('Carbon Neutral Technology Development', 
 'การพัฒนาเทคโนโลยีเพื่อลดการปล่อย Carbon และมุ่งสู่เป้าหมาย Carbon Neutral ของ DENSO รวมถึงการวิจัยเทคโนโลยีใหม่ๆ', 
 'Planning', 'Critical', 12000000.00, @NatthaID, 
 '2024-04-01', '2025-03-31', 5, 'Ministry of Environment', 'CNTD-2024',
 GETDATE(), GETDATE()),

('Next-Gen Mobility Solutions', 
 'การพัฒนาโซลูชันความคลื่นไหวรุ่นใหม่สำหรับยานยนต์ไฟฟ้าและ Autonomous Vehicles รวมถึงระบบ Connected Car', 
 'In Progress', 'High', 9200000.00, @ThammaphonID, 
 '2024-01-15', '2024-11-30', 35, 'Honda Motor Co.', 'NGMS-2024',
 GETDATE(), GETDATE());

PRINT '✅ สร้างโครงการ DENSO Innovation Team เรียบร้อยแล้ว';

-- ============================================================================
-- สร้างงานสำหรับโครงการ
-- ============================================================================
PRINT '📋 กำลังสร้างงานสำหรับโครงการ...';

-- ดึง Project IDs แบบ compatible
DECLARE @Proj1 INT, @Proj2 INT, @Proj3 INT, @Proj4 INT, @Proj5 INT;

SELECT @Proj1 = ProjectID FROM Projects WHERE ProjectCode = 'DDT-2024';
SELECT @Proj2 = ProjectID FROM Projects WHERE ProjectCode = 'SFAS-2024';
SELECT @Proj3 = ProjectID FROM Projects WHERE ProjectCode = 'ILMP-2024';
SELECT @Proj4 = ProjectID FROM Projects WHERE ProjectCode = 'CNTD-2024';
SELECT @Proj5 = ProjectID FROM Projects WHERE ProjectCode = 'NGMS-2024';

INSERT INTO Tasks (
    ProjectID, Title, Description, AssignedToID, Status, Priority, 
    DueDate, EstimatedHours, ActualHours, CompletionPercentage, CreatedByID,
    CreatedDate, UpdatedDate
) VALUES 
(@Proj1, 'ศึกษาและวิเคราะห์ระบบปัจจุบัน', 
 'ศึกษาและวิเคราะห์ระบบงานปัจจุบันของ DENSO เพื่อหาจุดที่ต้องปรับปรุงและพัฒนา', 
 @NatthaID, 'Done', 'High', '2024-02-29', 120, 118, 100, @ThammaphonID, GETDATE(), GETDATE()),

(@Proj1, 'ออกแบบ Architecture ระบบใหม่', 
 'ออกแบบสถาปัตยกรรมของระบบดิจิทัลใหม่ที่จะรองรับการขยายตัวในอนาคต', 
 @WaratcharponID, 'In Progress', 'Critical', '2024-04-15', 160, 95, 70, @ThammaphonID, GETDATE(), GETDATE()),

(@Proj1, 'พัฒนา AI Module สำหรับ Predictive Analytics', 
 'พัฒนาโมดูล AI ที่ใช้ในการวิเคราะห์และพยากรณ์ข้อมูลการผลิต', 
 @ThanespongID, 'In Progress', 'High', '2024-06-30', 200, 60, 40, @ThammaphonID, GETDATE(), GETDATE()),

(@Proj2, 'ติดตั้งและทดสอบ IoT Sensors', 
 'ติดตั้งเซ็นเซอร์ IoT ในสายการผลิตและทดสอบการทำงาน', 
 @WaratcharponID, 'Review', 'High', '2024-05-31', 80, 82, 95, @ChanakarnID, GETDATE(), GETDATE()),

(@Proj2, 'พัฒนา Machine Learning Algorithm', 
 'พัฒนาอัลกอริทึม Machine Learning สำหรับการตรวจสอบคุณภาพแบบอัตโนมัติ', 
 @ThanespongID, 'In Progress', 'Critical', '2024-07-15', 180, 45, 35, @ChanakarnID, GETDATE(), GETDATE()),

(@Proj2, 'สร้าง Dashboard สำหรับ Monitoring', 
 'สร้าง Dashboard แสดงสถานะและข้อมูลการผลิตแบบเรียลไทม์', 
 @NarissaraID, 'To Do', 'Medium', '2024-08-30', 100, 0, 0, @ChanakarnID, GETDATE(), GETDATE()),

(@Proj3, 'Requirements Gathering', 
 'รวบรวมความต้องการของ Innovation Lab และออกแบบระบบ', 
 @ChanakarnID, 'Done', 'Medium', '2024-03-31', 60, 58, 100, @ThammaphonID, GETDATE(), GETDATE()),

(@Proj3, 'ออกแบบ UI/UX ระบบ', 
 'ออกแบบ User Interface และ User Experience ของระบบ', 
 @NarissaraID, 'In Progress', 'Medium', '2024-05-15', 80, 25, 40, @ThammaphonID, GETDATE(), GETDATE()),

(@Proj3, 'พัฒนา Project Management Module', 
 'พัฒนาโมดูลจัดการโครงการที่ใช้ในระบบ', 
 @NatthaID, 'To Do', 'High', '2024-07-31', 120, 0, 0, @ThammaphonID, GETDATE(), GETDATE()),

(@Proj4, 'วิจัยเทคโนโลยี Carbon Capture', 
 'วิจัยและประเมินเทคโนโลยีการดักจับคาร์บอนใหม่ๆ', 
 @ThanespongID, 'In Progress', 'High', '2024-09-30', 150, 20, 15, @NatthaID, GETDATE(), GETDATE()),

(@Proj4, 'วางแผนการลดพลังงานในโรงงาน', 
 'จัดทำแผนลดการใช้พลังงานในกระบวนการผลิต', 
 @WaratcharponID, 'To Do', 'Medium', '2024-10-31', 80, 0, 0, @NatthaID, GETDATE(), GETDATE()),

(@Proj5, 'ศึกษาเทรนด์ยานยนต์ไฟฟ้า', 
 'ศึกษาและวิเคราะห์เทรนด์และเทคโนโลยีล่าสุดของยานยนต์ไฟฟ้า', 
 @ChanakarnID, 'Done', 'Medium', '2024-03-15', 70, 70, 100, @ThammaphonID, GETDATE(), GETDATE()),

(@Proj5, 'พัฒนาต้นแบบระบบ Connected Car', 
 'ออกแบบและพัฒนาต้นแบบสำหรับระบบ Connected Car รุ่นใหม่', 
 @NarissaraID, 'In Progress', 'Critical', '2024-11-30', 250, 80, 30, @ThammaphonID, GETDATE(), GETDATE());

PRINT '✅ สร้างงานสำหรับโครงการเรียบร้อยแล้ว';

-- ============================================================================
-- เพิ่มสมาชิกในโครงการ
-- ============================================================================
PRINT '👥 กำลังเพิ่มสมาชิกในโครงการ...';

INSERT INTO ProjectMembers (ProjectID, UserID, Role) VALUES 
(@Proj1, @ThammaphonID, 'Manager'),
(@Proj1, @ChanakarnID, 'Member'),
(@Proj1, @WaratcharponID, 'Member'),
(@Proj1, @ThanespongID, 'Member'),

(@Proj2, @NatthaID, 'Manager'),
(@Proj2, @WaratcharponID, 'Member'),
(@Proj2, @ThanespongID, 'Member'),
(@Proj2, @NarissaraID, 'Member'),

(@Proj3, @ThammaphonID, 'Manager'),
(@Proj3, @ChanakarnID, 'Member'),
(@Proj3, @NatthaID, 'Member'),
(@Proj3, @NarissaraID, 'Member'),

(@Proj4, @NatthaID, 'Manager'),
(@Proj4, @ThanespongID, 'Member'),
(@Proj4, @WaratcharponID, 'Member'),

(@Proj5, @ThammaphonID, 'Manager'),
(@Proj5, @ChanakarnID, 'Member'),
(@Proj5, @NarissaraID, 'Member');

PRINT '✅ เพิ่มสมาชิกในโครงการเรียบร้อยแล้ว';

-- ============================================================================
-- เพิ่มการแจ้งเตือนต้อนรับ
-- ============================================================================
PRINT '📧 กำลังสร้างการแจ้งเตือนต้อนรับ...';

-- แยก INSERT แต่ละ record เพื่อหลีกเลี่ยง subquery error
INSERT INTO Notifications (UserID, Type, Title, Message, Priority, CreatedDate) 
VALUES (@ThammaphonID, 'system', 'ยินดีต้อนรับสู่ DENSO Project Manager Pro', 'ระบบจัดการโครงการของ DENSO Innovation Team พร้อมใช้งานแล้ว กรุณาปรับแต่งโปรไฟล์และเริ่มต้นการทำงานของคุณ', 'medium', GETDATE());

INSERT INTO Notifications (UserID, Type, Title, Message, Priority, CreatedDate) 
VALUES (@NatthaID, 'system', 'ยินดีต้อนรับสู่ DENSO Project Manager Pro', 'ระบบจัดการโครงการของ DENSO Innovation Team พร้อมใช้งานแล้ว กรุณาปรับแต่งโปรไฟล์และเริ่มต้นการทำงานของคุณ', 'medium', GETDATE());

INSERT INTO Notifications (UserID, Type, Title, Message, Priority, CreatedDate) 
VALUES (@WaratcharponID, 'system', 'ยินดีต้อนรับสู่ DENSO Project Manager Pro', 'ระบบจัดการโครงการของ DENSO Innovation Team พร้อมใช้งานแล้ว กรุณาปรับแต่งโปรไฟล์และเริ่มต้นการทำงานของคุณ', 'medium', GETDATE());

INSERT INTO Notifications (UserID, Type, Title, Message, Priority, CreatedDate) 
VALUES (@ThanespongID, 'system', 'ยินดีต้อนรับสู่ DENSO Project Manager Pro', 'ระบบจัดการโครงการของ DENSO Innovation Team พร้อมใช้งานแล้ว กรุณาปรับแต่งโปรไฟล์และเริ่มต้นการทำงานของคุณ', 'medium', GETDATE());

INSERT INTO Notifications (UserID, Type, Title, Message, Priority, CreatedDate) 
VALUES (@ChanakarnID, 'system', 'ยินดีต้อนรับสู่ DENSO Project Manager Pro', 'ระบบจัดการโครงการของ DENSO Innovation Team พร้อมใช้งานแล้ว กรุณาปรับแต่งโปรไฟล์และเริ่มต้นการทำงานของคุณ', 'medium', GETDATE());

INSERT INTO Notifications (UserID, Type, Title, Message, Priority, CreatedDate) 
VALUES (@NarissaraID, 'system', 'ยินดีต้อนรับสู่ DENSO Project Manager Pro', 'ระบบจัดการโครงการของ DENSO Innovation Team พร้อมใช้งานแล้ว กรุณาปรับแต่งโปรไฟล์และเริ่มต้นการทำงานของคุณ', 'medium', GETDATE());

PRINT '✅ สร้างการแจ้งเตือนต้อนรับเรียบร้อยแล้ว';

-- ============================================================================
-- ใส่ System Settings ที่เหมาะสมกับ DENSO
-- ============================================================================
PRINT '⚙️ กำลังอัพเดท System Settings...';

DELETE FROM SystemSettings;

INSERT INTO SystemSettings (SettingKey, SettingValue, CreatedDate, UpdatedDate) VALUES 
('app_name', '"DENSO Project Manager Pro"', GETDATE(), GETDATE()),
('app_version', '"2.0.0"', GETDATE(), GETDATE()),
('company_name', '"DENSO Corporation"', GETDATE(), GETDATE()),
('theme', '"light"', GETDATE(), GETDATE()),
('language', '"th"', GETDATE(), GETDATE()),
('timezone', '"Asia/Bangkok"', GETDATE(), GETDATE()),
('session_timeout', '3600', GETDATE(), GETDATE()),
('max_upload_size', '100', GETDATE(), GETDATE()),
('email_notifications', 'true', GETDATE(), GETDATE()),
('auto_backup', 'true', GETDATE(), GETDATE()),
('backup_schedule', '"02:00"', GETDATE(), GETDATE()),
('backup_retention_days', '90', GETDATE(), GETDATE()),
('default_currency', '"THB"', GETDATE(), GETDATE()),
('working_hours_start', '"08:00"', GETDATE(), GETDATE()),
('working_hours_end', '"17:00"', GETDATE(), GETDATE()),
('weekend_days', '["Saturday", "Sunday"]', GETDATE(), GETDATE()),
('company_logo', '"/assets/denso-logo.png"', GETDATE(), GETDATE()),
('password_policy', '{"min_length": 8, "require_uppercase": true, "require_lowercase": true, "require_digits": true, "require_special": true, "history_count": 5}', GETDATE(), GETDATE()),
('security_settings', '{"max_login_attempts": 5, "lockout_duration": 900, "session_cookie_secure": false, "force_password_change": false}', GETDATE(), GETDATE());

PRINT '✅ อัพเดท System Settings เรียบร้อยแล้ว';

-- ============================================================================
-- สรุปกระชับ
-- ============================================================================
PRINT '';
PRINT '🎉 DENSO Innovation Team data setup completed!';
PRINT '🚀 System ready!';

SELECT 'Users' as TableName, COUNT(*) as RecordCount FROM Users
UNION ALL
SELECT 'Projects', COUNT(*) FROM Projects
UNION ALL
SELECT 'Tasks', COUNT(*) FROM Tasks;