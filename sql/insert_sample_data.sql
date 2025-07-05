USE SDXProjectManager;
GO

PRINT '🔄 เริ่มการลบข้อมูลเก่าและใส่ข้อมูลจริงของ DENSO Innovation Team...';

-- ============================================================================
-- ลบข้อมูลเก่าทั้งหมด (ตามลำดับ Foreign Key)
-- ============================================================================
DELETE FROM SystemSettings;
DELETE FROM Notifications;
DELETE FROM ProjectMembers;
DELETE FROM Tasks;
DELETE FROM Projects;
DELETE FROM Users;

PRINT '🗑️ ลบข้อมูลเก่าเรียบร้อยแล้ว';

-- ============================================================================
-- สร้างผู้ใช้จริงของ DENSO Innovation Team
-- ============================================================================
PRINT '👥 กำลังสร้างผู้ใช้ DENSO Innovation Team...';

INSERT INTO Users (
    Username, PasswordHash, Email, FirstName, LastName, Role, Department, 
    Phone, IsActive, CreatedDate
) VALUES
-- Hash สำหรับ Thammaphon@TS00029
('TS00029', '$2b$12$Q76.TWyVU2B64FDdRa7KPeREDLqf1FmzJEVil2x0Nlir9xNIgsMK6', 
 'thammaphon.chittasuwanna.a3q@ap.denso.com', 'Thammaphon', 'Chittasuwanna', 'Admin', 'Innovation', 
 '', 1, GETDATE()),

-- Hash สำหรับ Nattha@03954  
('03954', '$2b$12$vT9ehjENKY8SNVutUQ7wReRSHfBktF2GAM2GCvFUhlrocgYgeMa6e', 
 'nattha.pokasombut.a6s@ap.denso.com', 'Nattha', 'Pokasombut', 'Admin', 'Innovation', 
 '', 1, GETDATE()),

-- Hash สำหรับ Waratcharpon@05600
('05600', '$2b$12$rjwDgWa2bWhnCwWtgUPMtehoAFgwcQtC7h3PgW3jW9FteZIjZGJxy', 
 'waratcharpon.ponpiya.a8t@ap.denso.com', 'Waratcharpon', 'Ponpiya', 'Admin', 'Innovation', 
 '', 1, GETDATE()),

-- Hash สำหรับ Thanespong@FS00055
('FS00055', '$2b$12$.lDiiBS1Nl1RxThKzz72kueArHGH3nmSyjMIh84IkQpCINZIXb1L.', 
 'thanespong.obchey.a3y@ap.denso.com', 'Thanespong', 'Obchey', 'Admin', 'Innovation', 
 '', 1, GETDATE()),

-- Hash สำหรับ Chanakarn@TN00242
('TN00242', '$2b$12$foD0AbVzIWJznaQuQwxx/.yvJeaFV.DLRlyzkE18RP0ZJDcTO4s8q', 
 'chanakarn.patinung.a3m@ap.denso.com', 'Chanakarn', 'Patinung', 'Manager', 'Innovation', 
 '', 1, GETDATE()),

-- Hash สำหรับ Narissara@TN00243
('TN00243', '$2b$12$IxQbKirlCdqsmuwXNbtCSeUN7FdrqIC4m2JUI1J131YkC1WfDKhIC', 
 'narissara.lam-on.a8e@ap.denso.com', 'Narissara', 'Lam-on', 'User', 'Innovation', 
 '', 1, GETDATE());

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
    ProjectName, Description, Status, Priority, Budget, ManagerID, 
    StartDate, EndDate, CreatedDate, UpdatedDate
) VALUES 
('DENSO Digital Transformation Initiative', 
 'การปรับปรุงระบบดิจิทัลและกระบวนการทำงานของ DENSO เพื่อเพิ่มประสิทธิภาพและลดต้นทุน รวมถึงการพัฒนา AI และ IoT solutions สำหรับโรงงาน', 
 'Active', 'Critical', 15000000.00, @ThammaphonID, 
 '2024-01-01', '2024-12-31', GETDATE(), GETDATE()),

('Smart Factory Automation System', 
 'ระบบอัตโนมัติโรงงานอัจฉริยะที่ใช้ AI และ Machine Learning ในการควบคุมสายการผลิต ตรวจสอบคุณภาพ และบำรุงรักษาเชิงพยากรณ์', 
 'Active', 'High', 8500000.00, @NatthaID, 
 '2024-02-15', '2024-10-30', GETDATE(), GETDATE()),

('Innovation Lab Management Platform', 
 'แพลตฟอร์มจัดการ Innovation Lab ที่รวมระบบจัดการโครงการ การติดตามความคืบหน้า และการรายงานผลสำหรับทีม Innovation', 
 'Active', 'Medium', 2800000.00, @ThammaphonID, 
 '2024-03-01', '2024-08-31', GETDATE(), GETDATE()),

('Carbon Neutral Technology Development', 
 'การพัฒนาเทคโนโลยีเพื่อลดการปล่อย Carbon และมุ่งสู่เป้าหมาย Carbon Neutral ของ DENSO รวมถึงการวิจัยเทคโนโลยีใหม่ๆ', 
 'Active', 'Critical', 12000000.00, @NatthaID, 
 '2024-04-01', '2025-03-31', GETDATE(), GETDATE()),

('Next-Gen Mobility Solutions', 
 'การพัฒนาโซลูชันความคลื่นไหวรุ่นใหม่สำหรับยานยนต์ไฟฟ้าและ Autonomous Vehicles รวมถึงระบบ Connected Car', 
 'Active', 'High', 9200000.00, @ThammaphonID, 
 '2024-01-15', '2024-11-30', GETDATE(), GETDATE());

PRINT '✅ สร้างโครงการ DENSO Innovation Team เรียบร้อยแล้ว';

-- ============================================================================
-- สร้างงานสำหรับโครงการ
-- ============================================================================
PRINT '📋 กำลังสร้างงานสำหรับโครงการ...';

-- ดึง Project IDs
DECLARE @Proj1 INT, @Proj2 INT, @Proj3 INT, @Proj4 INT, @Proj5 INT;

SELECT @Proj1 = ProjectID FROM Projects WHERE ProjectName = 'DENSO Digital Transformation Initiative';
SELECT @Proj2 = ProjectID FROM Projects WHERE ProjectName = 'Smart Factory Automation System';
SELECT @Proj3 = ProjectID FROM Projects WHERE ProjectName = 'Innovation Lab Management Platform';
SELECT @Proj4 = ProjectID FROM Projects WHERE ProjectName = 'Carbon Neutral Technology Development';
SELECT @Proj5 = ProjectID FROM Projects WHERE ProjectName = 'Next-Gen Mobility Solutions';

INSERT INTO Tasks (
    ProjectID, TaskTitle, TaskDescription, AssignedTo, Status, Priority, 
    DueDate, EstimatedHours, ActualHours, CreatedDate, UpdatedDate
) VALUES 
(@Proj1, 'ศึกษาและวิเคราะห์ระบบปัจจุบัน', 
 'ศึกษาและวิเคราะห์ระบบงานปัจจุบันของ DENSO เพื่อหาจุดที่ต้องปรับปรุงและพัฒนา', 
 @NatthaID, 'Done', 'High', '2024-02-29', 120, 118, GETDATE(), GETDATE()),

(@Proj1, 'ออกแบบ Architecture ระบบใหม่', 
 'ออกแบบสถาปัตยกรรมของระบบดิจิทัลใหม่ที่จะรองรับการขยายตัวในอนาคต', 
 @WaratcharponID, 'In Progress', 'High', '2024-04-15', 160, 95, GETDATE(), GETDATE()),

(@Proj1, 'พัฒนา AI Module สำหรับ Predictive Analytics', 
 'พัฒนาโมดูล AI ที่ใช้ในการวิเคราะห์และพยากรณ์ข้อมูลการผลิต', 
 @ThanespongID, 'In Progress', 'High', '2024-06-30', 200, 60, GETDATE(), GETDATE()),

(@Proj2, 'ติดตั้งและทดสอบ IoT Sensors', 
 'ติดตั้งเซ็นเซอร์ IoT ในสายการผลิตและทดสอบการทำงาน', 
 @WaratcharponID, 'Review', 'High', '2024-05-31', 80, 82, GETDATE(), GETDATE()),

(@Proj2, 'พัฒนา Machine Learning Algorithm', 
 'พัฒนาอัลกอริทึม Machine Learning สำหรับการตรวจสอบคุณภาพแบบอัตโนมัติ', 
 @ThanespongID, 'In Progress', 'High', '2024-07-15', 180, 45, GETDATE(), GETDATE()),

(@Proj2, 'สร้าง Dashboard สำหรับ Monitoring', 
 'สร้าง Dashboard แสดงสถานะและข้อมูลการผลิตแบบเรียลไทม์', 
 @NarissaraID, 'To Do', 'Medium', '2024-08-30', 100, 0, GETDATE(), GETDATE()),

(@Proj3, 'Requirements Gathering', 
 'รวบรวมความต้องการของ Innovation Lab และออกแบบระบบ', 
 @ChanakarnID, 'Done', 'Medium', '2024-03-31', 60, 58, GETDATE(), GETDATE()),

(@Proj3, 'ออกแบบ UI/UX ระบบ', 
 'ออกแบบ User Interface และ User Experience ของระบบ', 
 @NarissaraID, 'In Progress', 'Medium', '2024-05-15', 80, 25, GETDATE(), GETDATE()),

(@Proj3, 'พัฒนา Project Management Module', 
 'พัฒนาโมดูลจัดการโครงการที่ใช้ในระบบ', 
 @NatthaID, 'To Do', 'High', '2024-07-31', 120, 0, GETDATE(), GETDATE()),

(@Proj4, 'วิจัยเทคโนโลยี Carbon Capture', 
 'วิจัยและประเมินเทคโนโลยีการดักจับคาร์บอนใหม่ๆ', 
 @ThanespongID, 'In Progress', 'High', '2024-09-30', 150, 20, GETDATE(), GETDATE()),

(@Proj4, 'วางแผนการลดพลังงานในโรงงาน', 
 'จัดทำแผนลดการใช้พลังงานในกระบวนการผลิต', 
 @WaratcharponID, 'To Do', 'Medium', '2024-10-31', 80, 0, GETDATE(), GETDATE()),

(@Proj5, 'ศึกษาเทรนด์ยานยนต์ไฟฟ้า', 
 'ศึกษาและวิเคราะห์เทรนด์และเทคโนโลยีล่าสุดของยานยนต์ไฟฟ้า', 
 @ChanakarnID, 'Done', 'Medium', '2024-03-15', 70, 70, GETDATE(), GETDATE()),

(@Proj5, 'พัฒนาต้นแบบระบบ Connected Car', 
 'ออกแบบและพัฒนาต้นแบบสำหรับระบบ Connected Car รุ่นใหม่', 
 @NarissaraID, 'In Progress', 'High', '2024-11-30', 250, 80, GETDATE(), GETDATE());

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

INSERT INTO Notifications (UserID, Type, Title, Message, CreatedDate) 
VALUES (@ThammaphonID, 'Info', 'ยินดีต้อนรับสู่ SDX Project Manager', 'ระบบจัดการโครงการของ DENSO Innovation Team พร้อมใช้งานแล้ว กรุณาปรับแต่งโปรไฟล์และเริ่มต้นการทำงานของคุณ', GETDATE());

INSERT INTO Notifications (UserID, Type, Title, Message, CreatedDate) 
VALUES (@NatthaID, 'Info', 'ยินดีต้อนรับสู่ SDX Project Manager', 'ระบบจัดการโครงการของ DENSO Innovation Team พร้อมใช้งานแล้ว กรุณาปรับแต่งโปรไฟล์และเริ่มต้นการทำงานของคุณ', GETDATE());

INSERT INTO Notifications (UserID, Type, Title, Message, CreatedDate) 
VALUES (@WaratcharponID, 'Info', 'ยินดีต้อนรับสู่ SDX Project Manager', 'ระบบจัดการโครงการของ DENSO Innovation Team พร้อมใช้งานแล้ว กรุณาปรับแต่งโปรไฟล์และเริ่มต้นการทำงานของคุณ', GETDATE());

INSERT INTO Notifications (UserID, Type, Title, Message, CreatedDate) 
VALUES (@ThanespongID, 'Info', 'ยินดีต้อนรับสู่ SDX Project Manager', 'ระบบจัดการโครงการของ DENSO Innovation Team พร้อมใช้งานแล้ว กรุณาปรับแต่งโปรไฟล์และเริ่มต้นการทำงานของคุณ', GETDATE());

INSERT INTO Notifications (UserID, Type, Title, Message, CreatedDate) 
VALUES (@ChanakarnID, 'Info', 'ยินดีต้อนรับสู่ SDX Project Manager', 'ระบบจัดการโครงการของ DENSO Innovation Team พร้อมใช้งานแล้ว กรุณาปรับแต่งโปรไฟล์และเริ่มต้นการทำงานของคุณ', GETDATE());

INSERT INTO Notifications (UserID, Type, Title, Message, CreatedDate) 
VALUES (@NarissaraID, 'Info', 'ยินดีต้อนรับสู่ SDX Project Manager', 'ระบบจัดการโครงการของ DENSO Innovation Team พร้อมใช้งานแล้ว กรุณาปรับแต่งโปรไฟล์และเริ่มต้นการทำงานของคุณ', GETDATE());

PRINT '✅ สร้างการแจ้งเตือนต้อนรับเรียบร้อยแล้ว';

-- ============================================================================
-- ใส่ System Settings ที่เหมาะสมกับ DENSO
-- ============================================================================
PRINT '⚙️ กำลังอัพเดท System Settings...';

INSERT INTO SystemSettings (SettingKey, SettingValue, UpdatedDate, UpdatedBy) VALUES 
('app_name', 'SDX Project Manager', GETDATE(), @ThammaphonID),
('app_version', '2.0.0', GETDATE(), @ThammaphonID),
('company_name', 'DENSO Corporation', GETDATE(), @ThammaphonID),
('session_timeout', '3600', GETDATE(), @ThammaphonID),
('max_upload_size', '100', GETDATE(), @ThammaphonID),
('email_notifications', 'true', GETDATE(), @ThammaphonID),
('auto_backup', 'true', GETDATE(), @ThammaphonID),
('default_currency', 'THB', GETDATE(), @ThammaphonID),
('timezone', 'Asia/Bangkok', GETDATE(), @ThammaphonID),
('language', 'th', GETDATE(), @ThammaphonID);

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

-- ============================================================================
-- สรุปรหัสผ่านที่ใช้ในระบบ (สำหรับ reference เท่านั้น)
-- ============================================================================
PRINT '';
PRINT '📋 Password Reference (รหัสผ่านที่ใช้ในระบบ):';
PRINT '   TS00029  → Thammaphon@TS00029';
PRINT '   03954    → Nattha@03954';
PRINT '   05600    → Waratcharpon@05600';  
PRINT '   FS00055  → Thanespong@FS00055';
PRINT '   TN00242  → Chanakarn@TN00242';
PRINT '   TN00243  → Narissara@TN00243';
PRINT '';
PRINT '⚠️  Note: รหัสผ่านเหล่านี้ถูก hash แล้วในฐานข้อมูล';