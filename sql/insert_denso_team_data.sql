USE SDXProjectManager;
GO

PRINT N'🔄 เริ่มการลบข้อมูลเก่าและใส่ข้อมูลจริงของ DENSO Innovation Team...';

-- ============================================================================
-- ลบข้อมูลเก่าทั้งหมด (ตามลำดับ Foreign Key)
-- ============================================================================
DELETE FROM Settings WHERE SettingKey NOT IN ('app_name', 'app_version'); -- เก็บ system settings
DELETE FROM Notifications;
DELETE FROM TimeEntries;
DELETE FROM TaskComments; 
DELETE FROM ProjectMembers;
DELETE FROM Tasks;
DELETE FROM Projects;
DELETE FROM UserRoles;
DELETE FROM Users WHERE Username != 'admin'; -- เก็บ admin user

PRINT N'🗑️ ลบข้อมูลเก่าเรียบร้อยแล้ว';

-- ============================================================================
-- สร้างผู้ใช้จริงของ DENSO Innovation Team
-- ============================================================================
PRINT N'👥 กำลังสร้างผู้ใช้ DENSO Innovation Team...';

INSERT INTO Users (
    Username, PasswordHash, Email, FirstName, LastName, Role, Department, 
    Position, Phone, IsActive, CreatedDate, Language, Timezone
) VALUES
-- Hash สำหรับ Thammaphon@TS00029
('TS00029', '$2b$12$Q76.TWyVU2B64FDdRa7KPeREDLqf1FmzJEVil2x0Nlir9xNIgsMK6', 
 'thammaphon.chittasuwanna.a3q@ap.denso.com', N'Thammaphon', N'Chittasuwanna', 'Admin', N'Innovation', 
 N'Innovation Manager', '', 1, GETDATE(), 'th', 'Asia/Bangkok'),

-- Hash สำหรับ Nattha@03954  
('03954', '$2b$12$vT9ehjENKY8SNVutUQ7wReRSHfBktF2GAM2GCvFUhlrocgYgeMa6e', 
 'nattha.pokasombut.a6s@ap.denso.com', N'Nattha', N'Pokasombut', 'Admin', N'Innovation', 
 N'Senior Innovation Engineer', '', 1, GETDATE(), 'th', 'Asia/Bangkok'),

-- Hash สำหรับ Waratcharpon@05600
('05600', '$2b$12$rjwDgWa2bWhnCwWtgUPMtehoAFgwcQtC7h3PgW3jW9FteZIjZGJxy', 
 'waratcharpon.ponpiya.a8t@ap.denso.com', N'Waratcharpon', N'Ponpiya', 'Admin', N'Innovation', 
 N'AI/ML Engineer', '', 1, GETDATE(), 'th', 'Asia/Bangkok'),

-- Hash สำหรับ Thanespong@FS00055
('FS00055', '$2b$12$.lDiiBS1Nl1RxThKzz72kueArHGH3nmSyjMIh84IkQpCINZIXb1L.', 
 'thanespong.obchey.a3y@ap.denso.com', N'Thanespong', N'Obchey', 'Admin', N'Innovation', 
 N'System Architect', '', 1, GETDATE(), 'th', 'Asia/Bangkok'),

-- Hash สำหรับ Chanakarn@TN00242
('TN00242', '$2b$12$foD0AbVzIWJznaQuQwxx/.yvJeaFV.DLRlyzkE18RP0ZJDcTO4s8q', 
 'chanakarn.patinung.a3m@ap.denso.com', N'Chanakarn', N'Patinung', 'Project Manager', N'Innovation', 
 N'Project Manager', '', 1, GETDATE(), 'th', 'Asia/Bangkok'),

-- Hash สำหรับ Narissara@TN00243
('TN00243', '$2b$12$IxQbKirlCdqsmuwXNbtCSeUN7FdrqIC4m2JUI1J131YkC1WfDKhIC', 
 'narissara.lam-on.a8e@ap.denso.com', N'Narissara', N'Lam-on', 'User', N'Innovation', 
 N'Innovation Specialist', '', 1, GETDATE(), 'th', 'Asia/Bangkok');

PRINT N'✅ สร้างผู้ใช้ DENSO Innovation Team เรียบร้อยแล้ว';

-- ============================================================================
-- สร้างโครงการจริงของ DENSO Innovation Team
-- ============================================================================
PRINT N'📁 กำลังสร้างโครงการของ DENSO Innovation Team...';

-- ดึง User IDs แบบ compatible กับ SSMS เก่า
DECLARE @ThammaphonID INT, @NatthaID INT, @ChanakarnID INT, @WaratcharponID INT, @ThanespongID INT, @NarissaraID INT;

SELECT @ThammaphonID = UserID FROM Users WHERE Username = 'TS00029';
SELECT @NatthaID = UserID FROM Users WHERE Username = '03954';
SELECT @ChanakarnID = UserID FROM Users WHERE Username = 'TN00242';
SELECT @WaratcharponID = UserID FROM Users WHERE Username = '05600';
SELECT @ThanespongID = UserID FROM Users WHERE Username = 'FS00055';
SELECT @NarissaraID = UserID FROM Users WHERE Username = 'TN00243';

INSERT INTO Projects (
    ProjectCode, ProjectName, Description, Status, Priority, Budget, ManagerID, 
    StartDate, EndDate, ProjectType, ProjectCategory, CreatedDate, UpdatedDate, CreatedBy
) VALUES 
('DENSO-DT-2024', N'DENSO Digital Transformation Initiative', 
 N'การปรับปรุงระบบดิจิทัลและกระบวนการทำงานของ DENSO เพื่อเพิ่มประสิทธิภาพและลดต้นทุน รวมถึงการพัฒนา AI และ IoT solutions สำหรับโรงงาน', 
 'Active', 'Critical', 15000000.00, @ThammaphonID, 
 '2024-01-01', '2024-12-31', N'Digital Transformation', N'Technology', GETDATE(), GETDATE(), @ThammaphonID),

('SMART-FAC-2024', N'Smart Factory Automation System', 
 N'ระบบอัตโนมัติโรงงานอัจฉริยะที่ใช้ AI และ Machine Learning ในการควบคุมสายการผลิต ตรวจสอบคุณภาพ และบำรุงรักษาเชิงพยากรณ์', 
 'Active', 'High', 8500000.00, @NatthaID, 
 '2024-02-15', '2024-10-30', N'Manufacturing', N'Automation', GETDATE(), GETDATE(), @NatthaID),

('INNO-LAB-2024', N'Innovation Lab Management Platform', 
 N'แพลตฟอร์มจัดการ Innovation Lab ที่รวมระบบจัดการโครงการ การติดตามความคืบหน้า และการรายงานผลสำหรับทีม Innovation', 
 'Active', 'Medium', 2800000.00, @ThammaphonID, 
 '2024-03-01', '2024-08-31', N'Software Development', N'Platform', GETDATE(), GETDATE(), @ThammaphonID),

('CARBON-NEUT-2024', N'Carbon Neutral Technology Development', 
 N'การพัฒนาเทคโนโลยีเพื่อลดการปล่อย Carbon และมุ่งสู่เป้าหมาย Carbon Neutral ของ DENSO รวมถึงการวิจัยเทคโนโลยีใหม่ๆ', 
 'Active', 'Critical', 12000000.00, @NatthaID, 
 '2024-04-01', '2025-03-31', N'Research & Development', N'Environment', GETDATE(), GETDATE(), @NatthaID),

('MOBILITY-2024', N'Next-Gen Mobility Solutions', 
 N'การพัฒนาโซลูชันความคลื่นไหวรุ่นใหม่สำหรับยานยนต์ไฟฟ้าและ Autonomous Vehicles รวมถึงระบบ Connected Car', 
 'Active', 'High', 9200000.00, @ThammaphonID, 
 '2024-01-15', '2024-11-30', N'Product Development', N'Automotive', GETDATE(), GETDATE(), @ThammaphonID);

PRINT N'✅ สร้างโครงการ DENSO Innovation Team เรียบร้อยแล้ว';

-- ============================================================================
-- สร้างงานสำหรับโครงการ
-- ============================================================================
PRINT N'📋 กำลังสร้างงานสำหรับโครงการ...';

-- ดึง Project IDs
DECLARE @Proj1 INT, @Proj2 INT, @Proj3 INT, @Proj4 INT, @Proj5 INT;

SELECT @Proj1 = ProjectID FROM Projects WHERE ProjectCode = 'DENSO-DT-2024';
SELECT @Proj2 = ProjectID FROM Projects WHERE ProjectCode = 'SMART-FAC-2024';
SELECT @Proj3 = ProjectID FROM Projects WHERE ProjectCode = 'INNO-LAB-2024';
SELECT @Proj4 = ProjectID FROM Projects WHERE ProjectCode = 'CARBON-NEUT-2024';
SELECT @Proj5 = ProjectID FROM Projects WHERE ProjectCode = 'MOBILITY-2024';

INSERT INTO Tasks (
    ProjectID, TaskCode, TaskTitle, TaskDescription, AssignedUserID, ReporterID, Status, Priority, 
    DueDate, EstimatedHours, ActualHours, Progress, TaskType, CreatedDate, UpdatedDate, CreatedBy
) VALUES 
(@Proj1, 'DT-001', N'ศึกษาและวิเคราะห์ระบบปัจจุบัน', 
 N'ศึกษาและวิเคราะห์ระบบงานปัจจุบันของ DENSO เพื่อหาจุดที่ต้องปรับปรุงและพัฒนา', 
 @NatthaID, @ThammaphonID, 'Done', 'High', '2024-02-29', 120, 118, 100.00, N'Analysis', GETDATE(), GETDATE(), @ThammaphonID),

(@Proj1, 'DT-002', N'ออกแบบ Architecture ระบบใหม่', 
 N'ออกแบบสถาปัตยกรรมของระบบดิจิทัลใหม่ที่จะรองรับการขยายตัวในอนาคต', 
 @WaratcharponID, @ThammaphonID, 'In Progress', 'High', '2024-04-15', 160, 95, 65.00, N'Design', GETDATE(), GETDATE(), @ThammaphonID),

(@Proj1, 'DT-003', N'พัฒนา AI Module สำหรับ Predictive Analytics', 
 N'พัฒนาโมดูล AI ที่ใช้ในการวิเคราะห์และพยากรณ์ข้อมูลการผลิต', 
 @ThanespongID, @ThammaphonID, 'In Progress', 'High', '2024-06-30', 200, 60, 30.00, N'Development', GETDATE(), GETDATE(), @ThammaphonID),

(@Proj2, 'SF-001', N'ติดตั้งและทดสอบ IoT Sensors', 
 N'ติดตั้งเซ็นเซอร์ IoT ในสายการผลิตและทดสอบการทำงาน', 
 @WaratcharponID, @NatthaID, 'Review', 'High', '2024-05-31', 80, 82, 90.00, N'Implementation', GETDATE(), GETDATE(), @NatthaID),

(@Proj2, 'SF-002', N'พัฒนา Machine Learning Algorithm', 
 N'พัฒนาอัลกอริทึม Machine Learning สำหรับการตรวจสอบคุณภาพแบบอัตโนมัติ', 
 @ThanespongID, @NatthaID, 'In Progress', 'High', '2024-07-15', 180, 45, 25.00, N'Development', GETDATE(), GETDATE(), @NatthaID),

(@Proj2, 'SF-003', N'สร้าง Dashboard สำหรับ Monitoring', 
 N'สร้าง Dashboard แสดงสถานะและข้อมูลการผลิตแบบเรียลไทม์', 
 @NarissaraID, @NatthaID, 'To Do', 'Medium', '2024-08-30', 100, 0, 0.00, N'Development', GETDATE(), GETDATE(), @NatthaID),

(@Proj3, 'IL-001', N'Requirements Gathering', 
 N'รวบรวมความต้องการของ Innovation Lab และออกแบบระบบ', 
 @ChanakarnID, @ThammaphonID, 'Done', 'Medium', '2024-03-31', 60, 58, 100.00, N'Analysis', GETDATE(), GETDATE(), @ThammaphonID),

(@Proj3, 'IL-002', N'ออกแบบ UI/UX ระบบ', 
 N'ออกแบบ User Interface และ User Experience ของระบบ', 
 @NarissaraID, @ThammaphonID, 'In Progress', 'Medium', '2024-05-15', 80, 25, 35.00, N'Design', GETDATE(), GETDATE(), @ThammaphonID),

(@Proj3, 'IL-003', N'พัฒนา Project Management Module', 
 N'พัฒนาโมดูลจัดการโครงการที่ใช้ในระบบ', 
 @NatthaID, @ThammaphonID, 'To Do', 'High', '2024-07-31', 120, 0, 0.00, N'Development', GETDATE(), GETDATE(), @ThammaphonID),

(@Proj4, 'CN-001', N'วิจัยเทคโนโลยี Carbon Capture', 
 N'วิจัยและประเมินเทคโนโลยีการดักจับคาร์บอนใหม่ๆ', 
 @ThanespongID, @NatthaID, 'In Progress', 'High', '2024-09-30', 150, 20, 15.00, N'Research', GETDATE(), GETDATE(), @NatthaID),

(@Proj4, 'CN-002', N'วางแผนการลดพลังงานในโรงงาน', 
 N'จัดทำแผนลดการใช้พลังงานในกระบวนการผลิต', 
 @WaratcharponID, @NatthaID, 'To Do', 'Medium', '2024-10-31', 80, 0, 0.00, N'Planning', GETDATE(), GETDATE(), @NatthaID),

(@Proj5, 'MOB-001', N'ศึกษาเทรนด์ยานยนต์ไฟฟ้า', 
 N'ศึกษาและวิเคราะห์เทรนด์และเทคโนโลยีล่าสุดของยานยนต์ไฟฟ้า', 
 @ChanakarnID, @ThammaphonID, 'Done', 'Medium', '2024-03-15', 70, 70, 100.00, N'Research', GETDATE(), GETDATE(), @ThammaphonID),

(@Proj5, 'MOB-002', N'พัฒนาต้นแบบระบบ Connected Car', 
 N'ออกแบบและพัฒนาต้นแบบสำหรับระบบ Connected Car รุ่นใหม่', 
 @NarissaraID, @ThammaphonID, 'In Progress', 'High', '2024-11-30', 250, 80, 35.00, N'Development', GETDATE(), GETDATE(), @ThammaphonID);

PRINT N'✅ สร้างงานสำหรับโครงการเรียบร้อยแล้ว';

-- ============================================================================
-- เพิ่มสมาชิกในโครงการ
-- ============================================================================
PRINT N'👥 กำลังเพิ่มสมาชิกในโครงการ...';

INSERT INTO ProjectMembers (ProjectID, UserID, Role, CanEditTasks, CanDeleteTasks, CanManageMembers, CanViewReports) VALUES 
(@Proj1, @ThammaphonID, N'Project Manager', 1, 1, 1, 1),
(@Proj1, @ChanakarnID, N'Team Member', 1, 0, 0, 1),
(@Proj1, @WaratcharponID, N'Developer', 1, 0, 0, 1),
(@Proj1, @ThanespongID, N'AI Specialist', 1, 0, 0, 1),

(@Proj2, @NatthaID, N'Project Manager', 1, 1, 1, 1),
(@Proj2, @WaratcharponID, N'IoT Engineer', 1, 0, 0, 1),
(@Proj2, @ThanespongID, N'ML Engineer', 1, 0, 0, 1),
(@Proj2, @NarissaraID, N'Frontend Developer', 1, 0, 0, 1),

(@Proj3, @ThammaphonID, N'Project Manager', 1, 1, 1, 1),
(@Proj3, @ChanakarnID, N'Business Analyst', 1, 0, 0, 1),
(@Proj3, @NatthaID, N'Backend Developer', 1, 0, 0, 1),
(@Proj3, @NarissaraID, N'UI/UX Designer', 1, 0, 0, 1),

(@Proj4, @NatthaID, N'Project Manager', 1, 1, 1, 1),
(@Proj4, @ThanespongID, N'Research Engineer', 1, 0, 0, 1),
(@Proj4, @WaratcharponID, N'System Engineer', 1, 0, 0, 1),

(@Proj5, @ThammaphonID, N'Project Manager', 1, 1, 1, 1),
(@Proj5, @ChanakarnID, N'Product Manager', 1, 0, 0, 1),
(@Proj5, @NarissaraID, N'Software Developer', 1, 0, 0, 1);

PRINT N'✅ เพิ่มสมาชิกในโครงการเรียบร้อยแล้ว';

-- ============================================================================
-- เพิ่ม Task Comments สำหรับความเป็นจริง
-- ============================================================================
PRINT N'💬 กำลังเพิ่ม Task Comments...';

INSERT INTO TaskComments (TaskID, UserID, Comment, CommentType, CreatedDate) VALUES
((SELECT TaskID FROM Tasks WHERE TaskCode = 'DT-001'), @NatthaID, N'วิเคราะห์ระบบเดิมเสร็จแล้ว พบจุดปรับปรุง 5 จุดหลัก ที่ส่งผลต่อประสิทธิภาพ', 'Comment', GETDATE()),
((SELECT TaskID FROM Tasks WHERE TaskCode = 'DT-002'), @WaratcharponID, N'ออกแบบ microservices architecture เสร็จ 65% กำลังทำ API design', 'Status Change', GETDATE()),
((SELECT TaskID FROM Tasks WHERE TaskCode = 'SF-001'), @WaratcharponID, N'ติดตั้ง sensors เสร็จแล้ว รอ QA team review การทำงาน', 'Comment', GETDATE()),
((SELECT TaskID FROM Tasks WHERE TaskCode = 'IL-001'), @ChanakarnID, N'รวบรวม requirements จากทุกแผนกเสร็จแล้ว สรุปเป็น 25 functional requirements', 'Comment', GETDATE()),
((SELECT TaskID FROM Tasks WHERE TaskCode = 'MOB-001'), @ChanakarnID, N'สรุปเทรนด์ EV market 2024: Tesla ยังคงนำ แต่ Chinese brands เติบโตเร็ว', 'Comment', GETDATE());

PRINT N'✅ เพิ่ม Task Comments เรียบร้อยแล้ว';

-- ============================================================================
-- เพิ่ม Time Entries สำหรับ tracking
-- ============================================================================
PRINT N'⏰ กำลังเพิ่ม Time Entries...';

INSERT INTO TimeEntries (TaskID, UserID, StartTime, EndTime, Duration, Description, IsBillable, CreatedDate) VALUES
((SELECT TaskID FROM Tasks WHERE TaskCode = 'DT-001'), @NatthaID, '2024-02-01 09:00:00', '2024-02-01 17:00:00', 8.0, N'วิเคราะห์ระบบ ERP ปัจจุบัน', 1, GETDATE()),
((SELECT TaskID FROM Tasks WHERE TaskCode = 'DT-002'), @WaratcharponID, '2024-03-15 09:00:00', '2024-03-15 12:00:00', 3.0, N'ออกแบบ API structure', 1, GETDATE()),
((SELECT TaskID FROM Tasks WHERE TaskCode = 'SF-001'), @WaratcharponID, '2024-04-10 08:00:00', '2024-04-10 16:00:00', 8.0, N'ติดตั้ง IoT sensors ในสายการผลิต A', 1, GETDATE()),
((SELECT TaskID FROM Tasks WHERE TaskCode = 'IL-002'), @NarissaraID, '2024-04-20 10:00:00', '2024-04-20 15:00:00', 5.0, N'ออกแบบ wireframe สำหรับ dashboard', 1, GETDATE()),
((SELECT TaskID FROM Tasks WHERE TaskCode = 'MOB-002'), @NarissaraID, '2024-05-01 09:00:00', '2024-05-01 17:00:00', 8.0, N'พัฒนา Connected Car mobile app prototype', 1, GETDATE());

PRINT N'✅ เพิ่ม Time Entries เรียบร้อยแล้ว';

-- ============================================================================
-- เพิ่มการแจ้งเตือนต้อนรับ
-- ============================================================================
PRINT N'📧 กำลังสร้างการแจ้งเตือนต้อนรับ...';

INSERT INTO Notifications (UserID, Title, Message, Type, Category, CreatedDate) VALUES 
(@ThammaphonID, N'ยินดีต้อนรับสู่ SDX Project Manager', N'ระบบจัดการโครงการของ DENSO Innovation Team พร้อมใช้งานแล้ว กรุณาปรับแต่งโปรไฟล์และเริ่มต้นการทำงานของคุณ', 'Info', 'System', GETDATE()),
(@NatthaID, N'ยินดีต้อนรับสู่ SDX Project Manager', N'ระบบจัดการโครงการของ DENSO Innovation Team พร้อมใช้งานแล้ว กรุณาปรับแต่งโปรไฟล์และเริ่มต้นการทำงานของคุณ', 'Info', 'System', GETDATE()),
(@WaratcharponID, N'ยินดีต้อนรับสู่ SDX Project Manager', N'ระบบจัดการโครงการของ DENSO Innovation Team พร้อมใช้งานแล้ว กรุณาปรับแต่งโปรไฟล์และเริ่มต้นการทำงานของคุณ', 'Info', 'System', GETDATE()),
(@ThanespongID, N'ยินดีต้อนรับสู่ SDX Project Manager', N'ระบบจัดการโครงการของ DENSO Innovation Team พร้อมใช้งานแล้ว กรุณาปรับแต่งโปรไฟล์และเริ่มต้นการทำงานของคุณ', 'Info', 'System', GETDATE()),
(@ChanakarnID, N'ยินดีต้อนรับสู่ SDX Project Manager', N'ระบบจัดการโครงการของ DENSO Innovation Team พร้อมใช้งานแล้ว กรุณาปรับแต่งโปรไฟล์และเริ่มต้นการทำงานของคุณ', 'Info', 'System', GETDATE()),
(@NarissaraID, N'ยินดีต้อนรับสู่ SDX Project Manager', N'ระบบจัดการโครงการของ DENSO Innovation Team พร้อมใช้งานแล้ว กรุณาปรับแต่งโปรไฟล์และเริ่มต้นการทำงานของคุณ', 'Info', 'System', GETDATE());

-- แจ้งเตือนงานที่กำลังจะครบกำหนด
INSERT INTO Notifications (UserID, Title, Message, Type, Category, CreatedDate) VALUES 
(@WaratcharponID, N'งานใกล้ครบกำหนด', N'งาน "ออกแบบ Architecture ระบบใหม่" จะครบกำหนดในอีก 5 วัน (15 เม.ย. 2024)', 'Warning', 'Task', GETDATE()),
(@ThanespongID, N'งานใหม่ถูกมอบหมาย', N'คุณได้รับมอบหมายงาน "วิจัยเทคโนโลยี Carbon Capture" ในโครงการ Carbon Neutral Technology Development', 'Info', 'Task', GETDATE()),
(@NarissaraID, N'อัปเดตความคืบหน้าโครงการ', N'โครงการ Innovation Lab Management Platform มีความคืบหน้า 45% แล้ว', 'Success', 'Project', GETDATE());

PRINT N'✅ สร้างการแจ้งเตือนต้อนรับเรียบร้อยแล้ว';

-- ============================================================================
-- อัปเดต Settings สำหรับ DENSO
-- ============================================================================
PRINT N'⚙️ กำลังอัปเดต System Settings สำหรับ DENSO...';

-- อัปเดต settings ที่มีอยู่แล้ว
UPDATE Settings SET 
    SettingValue = N'SDX Project Manager - DENSO Innovation Team',
    UpdatedDate = GETDATE(),
    UpdatedBy = @ThammaphonID
WHERE SettingKey = 'app_name';

UPDATE Settings SET 
    SettingValue = N'DENSO Corporation - Innovation Division',
    UpdatedDate = GETDATE(),
    UpdatedBy = @ThammaphonID
WHERE SettingKey = 'company_name';

-- เพิ่ม settings ใหม่สำหรับ DENSO
INSERT INTO Settings (SettingKey, SettingValue, SettingType, Category, Description, UpdatedBy, CreatedDate, UpdatedDate) VALUES 
('denso_division', N'Innovation Division', 'string', 'Application', N'แผนกที่ใช้ระบบ', @ThammaphonID, GETDATE(), GETDATE()),
('project_prefix', 'DENSO', 'string', 'Application', N'คำนำหน้าโครงการ', @ThammaphonID, GETDATE(), GETDATE()),
('fiscal_year_start', '04', 'integer', 'Application', N'เดือนเริ่มต้นปีงบประมาณ (เมษายน = 04)', @ThammaphonID, GETDATE(), GETDATE()),
('default_currency', 'THB', 'string', 'Application', N'สกุลเงินเริ่มต้น', @ThammaphonID, GETDATE(), GETDATE()),
('work_hours_per_day', '8', 'integer', 'System', N'จำนวนชั่วโมงทำงานต่อวัน', @ThammaphonID, GETDATE(), GETDATE()),
('notification_email_enabled', 'true', 'boolean', 'Notifications', N'เปิดใช้การส่งอีเมลแจ้งเตือน', @ThammaphonID, GETDATE(), GETDATE()),
('backup_schedule', 'daily', 'string', 'System', N'ตารางเวลาสำรองข้อมูล', @ThammaphonID, GETDATE(), GETDATE()),
('max_concurrent_users', '50', 'integer', 'Performance', N'จำนวนผู้ใช้พร้อมกันสูงสุด', @ThammaphonID, GETDATE(), GETDATE());

PRINT N'✅ อัปเดต System Settings เรียบร้อยแล้ว';

-- ============================================================================
-- สร้าง Project Metrics เริ่มต้น
-- ============================================================================
PRINT N'📊 กำลังสร้าง Project Metrics เริ่มต้น...';

INSERT INTO ProjectMetrics (
    ProjectID, SnapshotDate, TotalTasks, CompletedTasks, InProgressTasks, OverdueTasks,
    TotalEstimatedHours, TotalActualHours, BudgetSpent, TeamSize
) 
SELECT 
    p.ProjectID,
    CAST(GETDATE() AS DATE) as SnapshotDate,
    COUNT(t.TaskID) as TotalTasks,
    SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as CompletedTasks,
    SUM(CASE WHEN t.Status = 'In Progress' THEN 1 ELSE 0 END) as InProgressTasks,
    SUM(CASE WHEN t.DueDate < GETDATE() AND t.Status != 'Done' THEN 1 ELSE 0 END) as OverdueTasks,
    SUM(ISNULL(t.EstimatedHours, 0)) as TotalEstimatedHours,
    SUM(ISNULL(t.ActualHours, 0)) as TotalActualHours,
    p.ActualCost as BudgetSpent,
    COUNT(DISTINCT pm.UserID) as TeamSize
FROM Projects p
LEFT JOIN Tasks t ON p.ProjectID = t.ProjectID
LEFT JOIN ProjectMembers pm ON p.ProjectID = pm.ProjectID AND pm.IsActive = 1
GROUP BY p.ProjectID, p.ActualCost;

PRINT N'✅ สร้าง Project Metrics เรียบร้อยแล้ว';

-- ============================================================================
-- สร้าง User Metrics เริ่มต้น
-- ============================================================================
PRINT N'👤 กำลังสร้าง User Metrics เริ่มต้น...';

INSERT INTO UserMetrics (
    UserID, MetricDate, TasksCompleted, TasksCreated, HoursLogged, ProjectsActive
)
SELECT 
    u.UserID,
    CAST(GETDATE() AS DATE) as MetricDate,
    COUNT(CASE WHEN t.Status = 'Done' THEN 1 END) as TasksCompleted,
    COUNT(t.TaskID) as TasksCreated,
    SUM(ISNULL(te.Duration, 0)) as HoursLogged,
    COUNT(DISTINCT pm.ProjectID) as ProjectsActive
FROM Users u
LEFT JOIN Tasks t ON u.UserID = t.AssignedUserID
LEFT JOIN TimeEntries te ON u.UserID = te.UserID
LEFT JOIN ProjectMembers pm ON u.UserID = pm.UserID AND pm.IsActive = 1
WHERE u.Username != 'admin'
GROUP BY u.UserID;

PRINT N'✅ สร้าง User Metrics เรียบร้อยแล้ว';

-- ============================================================================
-- อัปเดต Project Completion แบบ Manual (Fixed)
-- ============================================================================
PRINT N'📈 กำลังอัปเดต Project Completion Percentage...';

-- อัปเดตแต่ละโครงการ
EXEC sp_UpdateProjectCompletion @ProjectID = @Proj1;
EXEC sp_UpdateProjectCompletion @ProjectID = @Proj2;
EXEC sp_UpdateProjectCompletion @ProjectID = @Proj3;
EXEC sp_UpdateProjectCompletion @ProjectID = @Proj4;
EXEC sp_UpdateProjectCompletion @ProjectID = @Proj5;

PRINT N'✅ อัปเดต Project Completion เรียบร้อยแล้ว';

-- ============================================================================
-- สร้าง Custom Report เริ่มต้น
-- ============================================================================
PRINT N'📋 กำลังสร้าง Custom Reports เริ่มต้น...';

INSERT INTO CustomReports (
    ReportName, Description, ReportType, QueryDefinition, CreatedBy, CreatedDate, IsPublic
) VALUES
(N'DENSO Innovation Team Dashboard', 
 N'แดชบอร์ดภาพรวมสำหรับทีม Innovation ของ DENSO', 
 'Dashboard',
 '{"type": "dashboard", "widgets": ["project_status", "task_progress", "team_performance", "budget_overview"]}',
 @ThammaphonID, GETDATE(), 1),

(N'Weekly Progress Report', 
 N'รายงานความคืบหน้าประจำสัปดาห์', 
 'Report',
 '{"type": "report", "frequency": "weekly", "sections": ["project_summary", "completed_tasks", "upcoming_deadlines"]}',
 @ThammaphonID, GETDATE(), 1),

(N'Resource Utilization Analysis', 
 N'การวิเคราะห์การใช้ทรัพยากรทีมงาน', 
 'Chart',
 '{"type": "chart", "chart_type": "bar", "data_source": "user_metrics", "groupby": "department"}',
 @NatthaID, GETDATE(), 0);

PRINT N'✅ สร้าง Custom Reports เรียบร้อยแล้ว';

-- ============================================================================
-- สร้าง Audit Log Entries เริ่มต้น
-- ============================================================================
PRINT N'📝 กำลังสร้าง Audit Log เริ่มต้น...';

INSERT INTO AuditLog (
    UserID, Action, EntityType, EntityID, EntityName, 
    NewValues, IPAddress, Timestamp, Result
) VALUES
(@ThammaphonID, 'CREATE', 'Project', @Proj1, N'DENSO Digital Transformation Initiative', 
 '{"status": "Active", "priority": "Critical", "budget": 15000000}', '192.168.1.100', GETDATE(), 'Success'),

(@NatthaID, 'CREATE', 'Project', @Proj2, N'Smart Factory Automation System', 
 '{"status": "Active", "priority": "High", "budget": 8500000}', '192.168.1.101', GETDATE(), 'Success'),

(@ThammaphonID, 'SYSTEM_SETUP', 'System', 1, N'DENSO Innovation Team Setup', 
 '{"users_created": 6, "projects_created": 5, "tasks_created": 13}', '192.168.1.100', GETDATE(), 'Success');

PRINT N'✅ สร้าง Audit Log เรียบร้อยแล้ว';

-- ============================================================================
-- สรุปและสถิติ
-- ============================================================================
PRINT N'';
PRINT N'🎉 ===============================================';
PRINT N'🎉 DENSO Innovation Team Setup Complete!';
PRINT N'🎉 ===============================================';
PRINT N'';

-- แสดงสถิติ
SELECT N'ตาราง' as Category, N'จำนวนข้อมูล' as Count
UNION ALL
SELECT N'Users', CAST(COUNT(*) AS NVARCHAR) FROM Users WHERE Username != 'admin'
UNION ALL
SELECT N'Projects', CAST(COUNT(*) AS NVARCHAR) FROM Projects
UNION ALL
SELECT N'Tasks', CAST(COUNT(*) AS NVARCHAR) FROM Tasks
UNION ALL
SELECT N'ProjectMembers', CAST(COUNT(*) AS NVARCHAR) FROM ProjectMembers
UNION ALL
SELECT N'Notifications', CAST(COUNT(*) AS NVARCHAR) FROM Notifications
UNION ALL
SELECT N'TimeEntries', CAST(COUNT(*) AS NVARCHAR) FROM TimeEntries
UNION ALL
SELECT N'TaskComments', CAST(COUNT(*) AS NVARCHAR) FROM TaskComments;

-- แสดงสรุปโครงการ
PRINT N'';
PRINT N'📊 สรุปโครงการ DENSO Innovation Team:';
SELECT 
    ProjectCode as N'รหัสโครงการ',
    ProjectName as N'ชื่อโครงการ', 
    Status as N'สถานะ',
    CONCAT(CAST(CompletionPercentage AS INT), '%') as N'ความคืบหน้า',
    CONCAT('฿', FORMAT(Budget, 'N0')) as N'งบประมาณ'
FROM Projects 
ORDER BY ProjectCode;

PRINT N'';
PRINT N'👥 ทีมงาน DENSO Innovation:';
SELECT 
    Username as N'Username',
    CONCAT(FirstName, ' ', LastName) as N'ชื่อ-นามสกุล',
    Position as N'ตำแหน่ง',
    Role as N'สิทธิ์ในระบบ'
FROM Users 
WHERE Username != 'admin'
ORDER BY Role DESC, FirstName;

PRINT N'';
PRINT N'📋 รหัสผ่านสำหรับทีมงาน:';
PRINT N'   TS00029  → Thammaphon@TS00029';
PRINT N'   03954    → Nattha@03954';
PRINT N'   05600    → Waratcharpon@05600';  
PRINT N'   FS00055  → Thanespong@FS00055';
PRINT N'   TN00242  → Chanakarn@TN00242';
PRINT N'   TN00243  → Narissara@TN00243';
PRINT N'';
PRINT N'⚠️  หมายเหตุ: รหัสผ่านเหล่านี้ถูกเข้ารหัสแล้วในฐานข้อมูล';
PRINT N'🔐 แนะนำให้เปลี่ยนรหัสผ่านหลังล็อกอินครั้งแรก';
PRINT N'';
PRINT N'🚀 ระบบพร้อมใช้งาน! สามารถเริ่มต้นได้ที่ http://localhost:8501';
PRINT N'📧 หากมีปัญหาติดต่อ: thammaphon.chittasuwanna.a3q@ap.denso.com';
PRINT N'';

-- สร้าง notification สำหรับ admin
INSERT INTO Notifications (UserID, Title, Message, Type, Category, CreatedDate) VALUES 
((SELECT UserID FROM Users WHERE Username = 'admin'), 
 N'DENSO Innovation Team Setup Complete', 
 N'ระบบได้ทำการ setup ข้อมูลทีม DENSO Innovation เรียบร้อยแล้ว มีผู้ใช้ใหม่ 6 คน โครงการ 5 โครงการ และงาน 13 งาน พร้อมใช้งาน', 
 'Success', 'System', GETDATE());

GO