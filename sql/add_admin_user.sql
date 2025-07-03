-- add_admin_user.sql
-- สำหรับเพิ่ม Admin User ใหม่

USE ProjectManagerDB;
GO

-- ตรวจสอบว่ามี admin user หรือยัง
PRINT '🔍 Checking for existing admin user...';

IF EXISTS (SELECT * FROM Users WHERE Username = 'admin')
BEGIN
    PRINT '⚠️ Admin user already exists';
    SELECT 
        Username, 
        Email, 
        FirstName, 
        LastName, 
        Role, 
        Department,
        IsActive,
        CreatedDate
    FROM Users 
    WHERE Username = 'admin';
END
ELSE
BEGIN
    PRINT '➕ Creating admin user...';
    
    -- Insert Default Admin User 
    -- Password: admin123 (hashed with bcrypt)
    INSERT INTO Users (
        Username, 
        PasswordHash, 
        Email, 
        FirstName, 
        LastName, 
        Role, 
        Department, 
        IsActive,
        CreatedDate,
        PasswordChangedDate
    )
    VALUES (
        'admin',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewLZ.9s5w8nTUOcG',
        'admin@denso.com',
        'System',
        'Administrator',
        'Admin',
        'IT',
        1,
        GETDATE(),
        GETDATE()
    );
    
    PRINT '✅ Default admin user created successfully!';
    PRINT '📝 Login Details:';
    PRINT '   Username: admin';
    PRINT '   Password: admin123';
    PRINT '   ⚠️ Please change password immediately after first login!';
END

-- แสดงข้อมูล admin user
PRINT '';
PRINT '👤 Current Admin User Info:';
SELECT 
    UserID,
    Username, 
    Email, 
    FirstName + ' ' + LastName as FullName,
    Role, 
    Department,
    IsActive,
    CreatedDate,
    LastLoginDate
FROM Users 
WHERE Username = 'admin';

-- ตรวจสอบจำนวน users ทั้งหมด
PRINT '';
PRINT '📊 Total Users in System:';
SELECT 
    COUNT(*) as TotalUsers,
    SUM(CASE WHEN IsActive = 1 THEN 1 ELSE 0 END) as ActiveUsers,
    SUM(CASE WHEN Role = 'Admin' THEN 1 ELSE 0 END) as AdminUsers
FROM Users;