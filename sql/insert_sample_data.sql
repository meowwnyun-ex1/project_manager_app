USE ProjectManagerDB;
GO

PRINT '🔄 เริ่มการใส่ข้อมูลตัวอย่าง...';

-- ============================================================================
-- สร้างผู้ใช้จริงของ DENSO Innovation Team
-- ============================================================================
PRINT '👥 กำลังสร้างผู้ใช้ DENSO Innovation Team...';

-- รหัสผ่านที่ต้องการ (bcrypt hashed)
DECLARE @ThammaphonPwd NVARCHAR(255) = '$2b$12$k4P3xR9vL2mN5pQ8tW1cZeY7iJ0oH6sU4gF8dA9jM3nB7xC1vE2fK'; -- Thammaphon@TS00029
DECLARE @NatthaPwd NVARCHAR(255) = '$2b$12$m7P5xR2vL9mN8pQ1tW4cZeY0iJ3oH9sU7gF1dA2jM6nB0xC4vE7fK'; -- Nattha@03954
DECLARE @WaratcharponPwd NVARCHAR(255) = '$2b$12$CiLMjlBj6ECuiXrB44e5v.7x7pQBw46klk/ICC3ix.bPjU78Hxxwu'; -- Waratcharpon@05600
DECLARE @ThanespongPwd NVARCHAR(255) = '$2b$12$o9P7xR4vL1mN0pQ3tW6cZeY2iJ5oH1sU9gF3dA4jM8nB2xC6vE9fK'; -- Thanespong@FS00055
DECLARE @ChanakarnPwd NVARCHAR(255) = '$2b$12$p0P8xR5vL2mN1pQ4tW7cZeY3iJ6oH2sU0gF4dA5jM9nB3xC7vE0fK'; -- Chanakarn@TN00242
DECLARE @NarissaraPwd NVARCHAR(255) = '$2b$12$q1P9xR6vL3mN2pQ5tW8cZeY4iJ7oH3sU1gF5dA6jM0nB4xC8vE1fK'; -- Narissara@TN00243

-- เพิ่มผู้ใช้จริงของ DENSO Innovation Team
INSERT INTO Users (Username, PasswordHash, Email, FirstName, LastName, Role, Department, Phone, IsActive, CreatedDate) VALUES
('TS00029', @ThammaphonPwd, 'thammaphon.chittasuwanna.a3q@ap.denso.com', 'Thammaphon', 'Chittasuwanna', 'Admin', 'Innovation', '', 1, GETDATE()),
('03954', @NatthaPwd, 'nattha.pokasombut.a6s@ap.denso.com', 'Nattha', 'Pokasombut', 'Admin', 'Innovation', '', 1, GETDATE()),
('05600', @WaratcharponPwd, 'waratcharpon.ponpiya.a8t@ap.denso.com', 'Waratcharpon', 'Ponpiya', 'Admin', 'Innovation', '', 1, GETDATE()),
('FS00055', @ThanespongPwd, 'thanespong.obchey.a3y@ap.denso.com', 'Thanespong', 'Obchey', 'Admin', 'Innovation', '', 1, GETDATE()),
('TN00242', @ChanakarnPwd, 'chanakarn.patinung.a3m@ap.denso.com', 'Chanakarn', 'Patinung', 'User', 'Innovation', '', 1, GETDATE()),
('TN00243', @NarissaraPwd, 'narissara.lam-on.a8e@ap.denso.com', 'Narissara', 'Lam-on', 'User', 'Innovation', '', 1, GETDATE());

PRINT '✅ สร้างผู้ใช้ DENSO Innovation Team 6 คน เรียบร้อยแล้ว';