-- setup.sql
-- DENSO Project Manager Pro - Complete Database Setup Script
-- Version: 2.0.0

USE master;
GO

-- Create Database if not exists
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'ProjectManagerDB')
BEGIN
    CREATE DATABASE ProjectManagerDB
    COLLATE SQL_Latin1_General_CP1_CI_AS;
    PRINT '✅ Database ProjectManagerDB created successfully';
END
ELSE
BEGIN
    PRINT 'ℹ️ Database ProjectManagerDB already exists';
END
GO

USE ProjectManagerDB;
GO

PRINT '🚀 Starting DENSO Project Manager Pro Database Setup...';
PRINT '================================================';

-- ============================================================================
-- USERS TABLE
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
BEGIN
    CREATE TABLE Users (
        UserID INT IDENTITY(1,1) PRIMARY KEY,
        Username NVARCHAR(100) UNIQUE NOT NULL,
        PasswordHash NVARCHAR(255) NOT NULL,
        Email NVARCHAR(255) UNIQUE NOT NULL,
        FirstName NVARCHAR(100),
        LastName NVARCHAR(100),
        Role NVARCHAR(50) DEFAULT 'User' CHECK (Role IN ('Admin', 'Manager', 'User', 'Viewer')),
        Department NVARCHAR(100),
        Phone NVARCHAR(20),
        Avatar NVARCHAR(500),
        IsActive BIT DEFAULT 1,
        CreatedDate DATETIME DEFAULT GETDATE(),
        LastLoginDate DATETIME,
        PasswordChangedDate DATETIME,
        ProfilePicture NVARCHAR(500),
        Bio NTEXT,
        Timezone NVARCHAR(50) DEFAULT 'UTC',
        Language NVARCHAR(10) DEFAULT 'en',
        Theme NVARCHAR(50) DEFAULT 'auto',
        NotificationSettings NTEXT, -- JSON string
        TwoFactorEnabled BIT DEFAULT 0,
        LoginAttempts INT DEFAULT 0,
        LockedUntil DATETIME NULL
    );
    PRINT '✅ Users table created';
END
GO

-- ============================================================================
-- PROJECTS TABLE
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Projects' AND xtype='U')
BEGIN
    CREATE TABLE Projects (
        ProjectID INT IDENTITY(1,1) PRIMARY KEY,
        ProjectName NVARCHAR(200) NOT NULL,
        Description NTEXT,
        StartDate DATE,
        EndDate DATE,
        Status NVARCHAR(50) DEFAULT 'Planning' CHECK (Status IN ('Planning', 'In Progress', 'Review', 'Completed', 'On Hold', 'Cancelled')),
        Priority NVARCHAR(50) DEFAULT 'Medium' CHECK (Priority IN ('Low', 'Medium', 'High', 'Critical')),
        Progress INT DEFAULT 0 CHECK (Progress >= 0 AND Progress <= 100),
        Budget DECIMAL(18,2),
        ActualBudget DECIMAL(18,2),
        EstimatedHours DECIMAL(8,2),
        ActualHours DECIMAL(8,2),
        ClientName NVARCHAR(200),
        CreatedBy INT NOT NULL,
        CreatedDate DATETIME DEFAULT GETDATE(),
        LastModifiedDate DATETIME DEFAULT GETDATE(),
        CompletedDate DATETIME,
        Tags NVARCHAR(500),
        ProjectCode NVARCHAR(20) UNIQUE,
        HealthScore DECIMAL(5,2) DEFAULT 0,
        RiskLevel NVARCHAR(20) DEFAULT 'Low' CHECK (RiskLevel IN ('Low', 'Medium', 'High', 'Critical')),
        FOREIGN KEY (CreatedBy) REFERENCES Users(UserID)
    );
    PRINT '✅ Projects table created';
END
GO

-- ============================================================================
-- TASKS TABLE
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Tasks' AND xtype='U')
BEGIN
    CREATE TABLE Tasks (
        TaskID INT IDENTITY(1,1) PRIMARY KEY,
        ProjectID INT NOT NULL,
        TaskName NVARCHAR(200) NOT NULL,
        Description NTEXT,
        StartDate DATE,
        EndDate DATE,
        DueDate DATE,
        AssigneeID INT,
        Status NVARCHAR(50) DEFAULT 'To Do' CHECK (Status IN ('To Do', 'In Progress', 'Review', 'Testing', 'Done', 'Cancelled', 'Blocked')),
        Priority NVARCHAR(50) DEFAULT 'Medium' CHECK (Priority IN ('Low', 'Medium', 'High', 'Critical')),
        Progress INT DEFAULT 0 CHECK (Progress >= 0 AND Progress <= 100),
        EstimatedHours DECIMAL(8,2),
        ActualHours DECIMAL(8,2),
        Dependencies NVARCHAR(500), -- Comma-separated TaskIDs
        Labels NVARCHAR(500), -- Comma-separated labels
        CreatedBy INT NOT NULL,
        CreatedDate DATETIME DEFAULT GETDATE(),
        LastModifiedDate DATETIME DEFAULT GETDATE(),
        CompletedDate DATETIME,
        Comments NTEXT,
        Attachments NTEXT, -- JSON string of file paths
        TaskCode NVARCHAR(20),
        StoryPoints INT DEFAULT 0,
        FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
        FOREIGN KEY (AssigneeID) REFERENCES Users(UserID),
        FOREIGN KEY (CreatedBy) REFERENCES Users(UserID)
    );
    PRINT '✅ Tasks table created';
END
GO

-- ============================================================================
-- PROJECT MEMBERS TABLE (Many-to-Many)
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ProjectMembers' AND xtype='U')
BEGIN
    CREATE TABLE ProjectMembers (
        ProjectMemberID INT IDENTITY(1,1) PRIMARY KEY,
        ProjectID INT NOT NULL,
        UserID INT NOT NULL,
        Role NVARCHAR(50) DEFAULT 'Member' CHECK (Role IN ('Owner', 'Manager', 'Member', 'Viewer')),
        JoinedDate DATETIME DEFAULT GETDATE(),
        FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
        FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE,
        UNIQUE(ProjectID, UserID)
    );
    PRINT '✅ ProjectMembers table created';
END
GO

-- ============================================================================
-- TIME TRACKING TABLE
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TimeTracking' AND xtype='U')
BEGIN
    CREATE TABLE TimeTracking (
        TimeTrackingID INT IDENTITY(1,1) PRIMARY KEY,
        TaskID INT NOT NULL,
        UserID INT NOT NULL,
        StartTime DATETIME NOT NULL,
        EndTime DATETIME,
        Duration DECIMAL(8,2), -- Hours
        Description NVARCHAR(500),
        CreatedDate DATETIME DEFAULT GETDATE(),
        FOREIGN KEY (TaskID) REFERENCES Tasks(TaskID) ON DELETE CASCADE,
        FOREIGN KEY (UserID) REFERENCES Users(UserID)
    );
    PRINT '✅ TimeTracking table created';
END
GO

-- ============================================================================
-- COMMENTS TABLE
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Comments' AND xtype='U')
BEGIN
    CREATE TABLE Comments (
        CommentID INT IDENTITY(1,1) PRIMARY KEY,
        EntityType NVARCHAR(50) NOT NULL CHECK (EntityType IN ('Project', 'Task')),
        EntityID INT NOT NULL,
        UserID INT NOT NULL,
        CommentText NTEXT NOT NULL,
        CreatedDate DATETIME DEFAULT GETDATE(),
        LastModifiedDate DATETIME DEFAULT GETDATE(),
        ParentCommentID INT, -- For nested comments
        IsEdited BIT DEFAULT 0,
        FOREIGN KEY (UserID) REFERENCES Users(UserID),
        FOREIGN KEY (ParentCommentID) REFERENCES Comments(CommentID)
    );
    PRINT '✅ Comments table created';
END
GO

-- ============================================================================
-- NOTIFICATIONS TABLE
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Notifications' AND xtype='U')
BEGIN
    CREATE TABLE Notifications (
        NotificationID INT IDENTITY(1,1) PRIMARY KEY,
        UserID INT NOT NULL,
        Type NVARCHAR(50) NOT NULL CHECK (Type IN ('info', 'success', 'warning', 'error', 'task', 'project', 'team', 'system')),
        Title NVARCHAR(200) NOT NULL,
        Message NTEXT NOT NULL,
        IsRead BIT DEFAULT 0,
        CreatedDate DATETIME DEFAULT GETDATE(),
        ReadDate DATETIME,
        ActionUrl NVARCHAR(500),
        ActionText NVARCHAR(100),
        Priority NVARCHAR(20) DEFAULT 'medium' CHECK (Priority IN ('low', 'medium', 'high', 'critical')),
        ExpiresAt DATETIME,
        FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
    );
    PRINT '✅ Notifications table created';
END
GO

-- ============================================================================
-- FILE ATTACHMENTS TABLE
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='FileAttachments' AND xtype='U')
BEGIN
    CREATE TABLE FileAttachments (
        AttachmentID INT IDENTITY(1,1) PRIMARY KEY,
        EntityType NVARCHAR(50) NOT NULL CHECK (EntityType IN ('Project', 'Task', 'Comment')),
        EntityID INT NOT NULL,
        FileName NVARCHAR(255) NOT NULL,
        OriginalFileName NVARCHAR(255) NOT NULL,
        FilePath NVARCHAR(500) NOT NULL,
        FileSize BIGINT NOT NULL,
        FileType NVARCHAR(100),
        MimeType NVARCHAR(100),
        UploadedBy INT NOT NULL,
        UploadedDate DATETIME DEFAULT GETDATE(),
        IsActive BIT DEFAULT 1,
        FOREIGN KEY (UploadedBy) REFERENCES Users(UserID)
    );
    PRINT '✅ FileAttachments table created';
END
GO

-- ============================================================================
-- AUDIT LOG TABLE
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='AuditLog' AND xtype='U')
BEGIN
    CREATE TABLE AuditLog (
        AuditID INT IDENTITY(1,1) PRIMARY KEY,
        UserID INT,
        Action NVARCHAR(100) NOT NULL,
        EntityType NVARCHAR(50),
        EntityID INT,
        OldValues NTEXT, -- JSON string
        NewValues NTEXT, -- JSON string
        IPAddress NVARCHAR(45),
        UserAgent NVARCHAR(500),
        CreatedDate DATETIME DEFAULT GETDATE(),
        FOREIGN KEY (UserID) REFERENCES Users(UserID)
    );
    PRINT '✅ AuditLog table created';
END
GO

-- ============================================================================
-- SETTINGS TABLE
-- ============================================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Settings' AND xtype='U')
BEGIN
    CREATE TABLE Settings (
        SettingID INT IDENTITY(1,1) PRIMARY KEY,
        SettingKey NVARCHAR(100) UNIQUE NOT NULL,
        SettingValue NTEXT,
        Description NVARCHAR(500),
        Category NVARCHAR(50) DEFAULT 'General',
        DataType NVARCHAR(20) DEFAULT 'string' CHECK (DataType IN ('string', 'number', 'boolean', 'json')),
        IsReadOnly BIT DEFAULT 0,
        CreatedDate DATETIME DEFAULT GETDATE(),
        LastModifiedDate DATETIME DEFAULT GETDATE()
    );
    PRINT '✅ Settings table created';
END
GO

-- ============================================================================
-- CREATE INDEXES FOR PERFORMANCE
-- ============================================================================
PRINT '📊 Creating indexes for optimal performance...';

-- Users indexes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Users_Username_IsActive')
    CREATE NONCLUSTERED INDEX IX_Users_Username_IsActive ON Users(Username, IsActive);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Users_Email')
    CREATE NONCLUSTERED INDEX IX_Users_Email ON Users(Email);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Users_Role_IsActive')
    CREATE NONCLUSTERED INDEX IX_Users_Role_IsActive ON Users(Role, IsActive);

-- Projects indexes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Projects_Status_Priority')
    CREATE NONCLUSTERED INDEX IX_Projects_Status_Priority ON Projects(Status, Priority);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Projects_CreatedBy')
    CREATE NONCLUSTERED INDEX IX_Projects_CreatedBy ON Projects(CreatedBy);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Projects_CreatedDate')
    CREATE NONCLUSTERED INDEX IX_Projects_CreatedDate ON Projects(CreatedDate);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Projects_EndDate')
    CREATE NONCLUSTERED INDEX IX_Projects_EndDate ON Projects(EndDate);

-- Tasks indexes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Tasks_ProjectID_Status')
    CREATE NONCLUSTERED INDEX IX_Tasks_ProjectID_Status ON Tasks(ProjectID, Status);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Tasks_AssigneeID_Status')
    CREATE NONCLUSTERED INDEX IX_Tasks_AssigneeID_Status ON Tasks(AssigneeID, Status);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Tasks_DueDate')
    CREATE NONCLUSTERED INDEX IX_Tasks_DueDate ON Tasks(DueDate);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Tasks_Priority_Status')
    CREATE NONCLUSTERED INDEX IX_Tasks_Priority_Status ON Tasks(Priority, Status);

-- Comments indexes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Comments_EntityType_EntityID')
    CREATE NONCLUSTERED INDEX IX_Comments_EntityType_EntityID ON Comments(EntityType, EntityID);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Comments_UserID_CreatedDate')
    CREATE NONCLUSTERED INDEX IX_Comments_UserID_CreatedDate ON Comments(UserID, CreatedDate);

-- Notifications indexes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Notifications_UserID_IsRead')
    CREATE NONCLUSTERED INDEX IX_Notifications_UserID_IsRead ON Notifications(UserID, IsRead);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_Notifications_CreatedDate')
    CREATE NONCLUSTERED INDEX IX_Notifications_CreatedDate ON Notifications(CreatedDate);

-- TimeTracking indexes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_TimeTracking_TaskID_UserID')
    CREATE NONCLUSTERED INDEX IX_TimeTracking_TaskID_UserID ON TimeTracking(TaskID, UserID);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_TimeTracking_StartTime')
    CREATE NONCLUSTERED INDEX IX_TimeTracking_StartTime ON TimeTracking(StartTime);

-- AuditLog indexes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_AuditLog_UserID_CreatedDate')
    CREATE NONCLUSTERED INDEX IX_AuditLog_UserID_CreatedDate ON AuditLog(UserID, CreatedDate);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_AuditLog_EntityType_EntityID')
    CREATE NONCLUSTERED INDEX IX_AuditLog_EntityType_EntityID ON AuditLog(EntityType, EntityID);

PRINT '✅ All performance indexes created';

-- ============================================================================
-- INSERT DEFAULT DATA
-- ============================================================================
PRINT '📝 Inserting default data...';

-- Insert Default Admin User (password is 'admin123' hashed with bcrypt)
IF NOT EXISTS (SELECT * FROM Users WHERE Username = 'admin')
BEGIN
    INSERT INTO Users (Username, PasswordHash, Email, FirstName, LastName, Role, Department, IsActive)
    VALUES (
        'admin',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewLZ.9s5w8nTUOcG',
        'admin@denso.com',
        'System',
        'Administrator',
        'Admin',
        'IT',
        1
    );
    PRINT '✅ Default admin user created (username: admin, password: admin123)';
END

-- Insert System Settings
IF NOT EXISTS (SELECT * FROM Settings WHERE SettingKey = 'app_version')
BEGIN
    INSERT INTO Settings (SettingKey, SettingValue, Description, Category, DataType) VALUES
    ('app_version', '2.0.0', 'Application version', 'System', 'string'),
    ('maintenance_mode', 'false', 'Enable maintenance mode', 'System', 'boolean'),
    ('max_upload_size', '50', 'Maximum file upload size in MB', 'Files', 'number'),
    ('session_timeout', '3600', 'Session timeout in seconds', 'Security', 'number'),
    ('enable_notifications', 'true', 'Enable system notifications', 'Features', 'boolean'),
    ('backup_retention_days', '90', 'Number of days to retain backups', 'Backup', 'number'),
    ('default_theme', 'auto', 'Default application theme', 'UI', 'string'),
    ('password_min_length', '8', 'Minimum password length', 'Security', 'number'),
    ('max_login_attempts', '5', 'Maximum failed login attempts', 'Security', 'number');
    
    PRINT '✅ System settings inserted';
END

-- Insert Sample Project (if no projects exist)
IF NOT EXISTS (SELECT * FROM Projects WHERE ProjectName = 'DENSO Project Manager Setup')
BEGIN
    DECLARE @AdminUserID INT = (SELECT UserID FROM Users WHERE Username = 'admin');
    
    INSERT INTO Projects (ProjectName, Description, StartDate, EndDate, Status, Priority, Budget, ClientName, CreatedBy, Progress)
    VALUES (
        'DENSO Project Manager Setup',
        'Initial setup and configuration of the DENSO Project Manager Pro system. This project includes database setup, user configuration, and system testing.',
        GETDATE(),
        DATEADD(DAY, 30, GETDATE()),
        'In Progress',
        'High',
        0.00,
        'DENSO Internal',
        @AdminUserID,
        75
    );
    
    DECLARE @ProjectID INT = SCOPE_IDENTITY();
    
    -- Insert sample tasks
    INSERT INTO Tasks (ProjectID, TaskName, Description, AssigneeID, Status, Priority, EstimatedHours, CreatedBy, Progress)
    VALUES 
    (@ProjectID, 'Database Schema Setup', 'Create and configure database tables, indexes, and initial data', @AdminUserID, 'Done', 'Critical', 4.0, @AdminUserID, 100),
    (@ProjectID, 'User Account Configuration', 'Set up initial user accounts and permissions', @AdminUserID, 'Done', 'High', 2.0, @AdminUserID, 100),
    (@ProjectID, 'System Testing', 'Test all system functionality and features', @AdminUserID, 'In Progress', 'Medium', 8.0, @AdminUserID, 50),
    (@ProjectID, 'Documentation Review', 'Review and finalize system documentation', @AdminUserID, 'To Do', 'Medium', 3.0, @AdminUserID, 0),
    (@ProjectID, 'Go-Live Preparation', 'Prepare system for production deployment', @AdminUserID, 'To Do', 'High', 6.0, @AdminUserID, 0);
    
    PRINT '✅ Sample project and tasks created';
END

-- Insert sample notification
IF NOT EXISTS (SELECT * FROM Notifications WHERE Title = 'Welcome to DENSO Project Manager Pro')
BEGIN
    DECLARE @AdminUserID INT = (SELECT UserID FROM Users WHERE Username = 'admin');
    
    INSERT INTO Notifications (UserID, Type, Title, Message, Priority)
    VALUES (
        @AdminUserID,
        'system',
        'Welcome to DENSO Project Manager Pro',
        'Your project management system has been successfully set up and is ready to use. Please change the default admin password and configure your preferences.',
        'high'
    );
    
    PRINT '✅ Welcome notification created';
END

-- ============================================================================
-- UPDATE STATISTICS FOR OPTIMAL PERFORMANCE
-- ============================================================================
PRINT '📈 Updating table statistics...';

UPDATE STATISTICS Users;
UPDATE STATISTICS Projects;
UPDATE STATISTICS Tasks;
UPDATE STATISTICS ProjectMembers;
UPDATE STATISTICS TimeTracking;
UPDATE STATISTICS Comments;
UPDATE STATISTICS Notifications;
UPDATE STATISTICS FileAttachments;
UPDATE STATISTICS AuditLog;
UPDATE STATISTICS Settings;

PRINT '✅ Statistics updated';

-- ============================================================================
-- CREATE VIEWS FOR COMMON QUERIES
-- ============================================================================
PRINT '👁️ Creating database views...';

-- Project Summary View
IF NOT EXISTS (SELECT * FROM sys.views WHERE name = 'vw_ProjectSummary')
BEGIN
    EXEC('
    CREATE VIEW vw_ProjectSummary AS
    SELECT 
        p.ProjectID,
        p.ProjectName,
        p.Description,
        p.Status,
        p.Priority,
        p.Progress,
        p.StartDate,
        p.EndDate,
        p.Budget,
        p.ActualBudget,
        p.CreatedDate,
        u.FirstName + '' '' + u.LastName as CreatorName,
        (SELECT COUNT(*) FROM Tasks WHERE ProjectID = p.ProjectID) as TotalTasks,
        (SELECT COUNT(*) FROM Tasks WHERE ProjectID = p.ProjectID AND Status = ''Done'') as CompletedTasks,
        (SELECT COUNT(*) FROM ProjectMembers WHERE ProjectID = p.ProjectID) as TeamSize
    FROM Projects p
    LEFT JOIN Users u ON p.CreatedBy = u.UserID
    WHERE p.Status != ''Cancelled''
    ');
    PRINT '✅ vw_ProjectSummary view created';
END

-- Task Summary View
IF NOT EXISTS (SELECT * FROM sys.views WHERE name = 'vw_TaskSummary')
BEGIN
    EXEC('
    CREATE VIEW vw_TaskSummary AS
    SELECT 
        t.TaskID,
        t.TaskName,
        t.Description,
        t.Status,
        t.Priority,
        t.Progress,
        t.DueDate,
        t.EstimatedHours,
        t.ActualHours,
        t.CreatedDate,
        p.ProjectName,
        assignee.FirstName + '' '' + assignee.LastName as AssigneeName,
        creator.FirstName + '' '' + creator.LastName as CreatorName,
        CASE 
            WHEN t.DueDate < CAST(GETDATE() AS DATE) AND t.Status NOT IN (''Done'', ''Cancelled'') THEN ''Overdue''
            WHEN t.DueDate = CAST(GETDATE() AS DATE) AND t.Status NOT IN (''Done'', ''Cancelled'') THEN ''Due Today''
            WHEN DATEDIFF(day, GETDATE(), t.DueDate) <= 3 AND t.Status NOT IN (''Done'', ''Cancelled'') THEN ''Due Soon''
            ELSE ''On Track''
        END as DueStatus
    FROM Tasks t
    LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
    LEFT JOIN Users assignee ON t.AssigneeID = assignee.UserID
    LEFT JOIN Users creator ON t.CreatedBy = creator.UserID
    ');
    PRINT '✅ vw_TaskSummary view created';
END

-- User Activity View
IF NOT EXISTS (SELECT * FROM sys.views WHERE name = 'vw_UserActivity')
BEGIN
    EXEC('
    CREATE VIEW vw_UserActivity AS
    SELECT 
        u.UserID,
        u.Username,
        u.FirstName + '' '' + u.LastName as FullName,
        u.Email,
        u.Role,
        u.Department,
        u.LastLoginDate,
        (SELECT COUNT(*) FROM Projects WHERE CreatedBy = u.UserID) as ProjectsCreated,
        (SELECT COUNT(*) FROM Tasks WHERE AssigneeID = u.UserID) as TasksAssigned,
        (SELECT COUNT(*) FROM Tasks WHERE AssigneeID = u.UserID AND Status = ''Done'') as TasksCompleted,
        (SELECT COUNT(*) FROM Comments WHERE UserID = u.UserID) as CommentsPosted
    FROM Users u
    WHERE u.IsActive = 1
    ');
    PRINT '✅ vw_UserActivity view created';
END

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================
PRINT '';
PRINT '🎉 DENSO Project Manager Pro Database Setup Complete!';
PRINT '================================================';
PRINT '✅ Database: ProjectManagerDB';
PRINT '✅ Tables: 9 core tables created';
PRINT '✅ Indexes: Performance indexes applied';
PRINT '✅ Views: Summary views created';
PRINT '✅ Admin User: admin / admin123';
PRINT '✅ Sample Data: Demo project and tasks';
PRINT '';
PRINT '🔑 Default Login Credentials:';
PRINT '   Username: admin';
PRINT '   Password: admin123';
PRINT '';
PRINT '⚠️  IMPORTANT: Change the default admin password immediately!';
PRINT '';
PRINT '🚀 Your DENSO Project Manager Pro is ready to use!';
PRINT '================================================';