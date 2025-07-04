-- setup.sql
-- DENSO Project Manager Pro - Clean Database Setup Script
-- Version: 2.0.3 (Production Ready - No Sample Data)

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

-- Drop existing tables if they exist (in correct order due to foreign keys)
IF OBJECT_ID('Tasks', 'U') IS NOT NULL DROP TABLE Tasks;
IF OBJECT_ID('ProjectMembers', 'U') IS NOT NULL DROP TABLE ProjectMembers;
IF OBJECT_ID('Projects', 'U') IS NOT NULL DROP TABLE Projects;
IF OBJECT_ID('TimeTracking', 'U') IS NOT NULL DROP TABLE TimeTracking;
IF OBJECT_ID('Comments', 'U') IS NOT NULL DROP TABLE Comments;
IF OBJECT_ID('Notifications', 'U') IS NOT NULL DROP TABLE Notifications;
IF OBJECT_ID('FileAttachments', 'U') IS NOT NULL DROP TABLE FileAttachments;
IF OBJECT_ID('AuditLog', 'U') IS NOT NULL DROP TABLE AuditLog;
IF OBJECT_ID('SystemSettings', 'U') IS NOT NULL DROP TABLE SystemSettings;
IF OBJECT_ID('Settings', 'U') IS NOT NULL DROP TABLE Settings;
IF OBJECT_ID('Users', 'U') IS NOT NULL DROP TABLE Users;

-- Drop views if they exist
IF OBJECT_ID('vw_ProjectSummary', 'V') IS NOT NULL DROP VIEW vw_ProjectSummary;
IF OBJECT_ID('vw_TaskSummary', 'V') IS NOT NULL DROP VIEW vw_TaskSummary;
IF OBJECT_ID('vw_UserActivity', 'V') IS NOT NULL DROP VIEW vw_UserActivity;
IF OBJECT_ID('ProjectOverview', 'V') IS NOT NULL DROP VIEW ProjectOverview;
IF OBJECT_ID('TaskOverview', 'V') IS NOT NULL DROP VIEW TaskOverview;

PRINT '🗑️ Cleaned up existing schema';
GO

-- ============================================================================
-- USERS TABLE (Compatible with auth.py and users.py)
-- ============================================================================
CREATE TABLE Users (
    UserID INT IDENTITY(1,1) PRIMARY KEY,
    Username NVARCHAR(50) UNIQUE NOT NULL,
    PasswordHash NVARCHAR(255) NOT NULL,
    Email NVARCHAR(100) UNIQUE NOT NULL,
    FirstName NVARCHAR(50) NOT NULL,
    LastName NVARCHAR(50) NOT NULL,
    Role NVARCHAR(20) DEFAULT 'User' CHECK (Role IN ('Admin', 'Project Manager', 'Team Lead', 'Developer', 'User', 'Viewer')),
    Department NVARCHAR(50),
    IsActive BIT DEFAULT 1,
    CreatedDate DATETIME DEFAULT GETDATE(),
    LastLoginDate DATETIME,
    FailedLoginAttempts INT DEFAULT 0,
    LastFailedLogin DATETIME,
    IsLocked BIT DEFAULT 0,
    MustChangePassword BIT DEFAULT 1,
    -- Additional fields from original schema
    Phone NVARCHAR(20),
    Avatar NVARCHAR(500),
    PasswordChangedDate DATETIME,
    ProfilePicture NVARCHAR(500),
    Bio NTEXT,
    Timezone NVARCHAR(50) DEFAULT 'Asia/Bangkok',
    Language NVARCHAR(10) DEFAULT 'th',
    Theme NVARCHAR(50) DEFAULT 'light',
    NotificationSettings NTEXT, -- JSON string
    TwoFactorEnabled BIT DEFAULT 0,
    LockedUntil DATETIME NULL
);

PRINT '✅ Users table created (compatible with auth.py)';
GO

-- ============================================================================
-- PROJECTS TABLE (Compatible with projects.py)
-- ============================================================================
CREATE TABLE Projects (
    ProjectID INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(100) NOT NULL, -- Used in projects.py
    Description NVARCHAR(MAX),
    StartDate DATE,
    EndDate DATE,
    Status NVARCHAR(20) DEFAULT 'Planning' CHECK (Status IN ('Planning', 'In Progress', 'On Hold', 'Completed', 'Cancelled')),
    Priority NVARCHAR(10) DEFAULT 'Medium' CHECK (Priority IN ('Low', 'Medium', 'High', 'Critical')),
    CompletionPercentage INT DEFAULT 0 CHECK (CompletionPercentage BETWEEN 0 AND 100),
    Budget DECIMAL(15,2),
    ActualCost DECIMAL(15,2) DEFAULT 0,
    EstimatedHours DECIMAL(8,2),
    ActualHours DECIMAL(8,2),
    ClientName NVARCHAR(100),
    ManagerID INT, -- Used in projects.py
    CreatedDate DATETIME DEFAULT GETDATE(),
    UpdatedDate DATETIME DEFAULT GETDATE(),
    CompletedDate DATETIME,
    -- Additional fields from original schema
    Tags NVARCHAR(500),
    ProjectCode NVARCHAR(20),
    HealthScore DECIMAL(5,2) DEFAULT 0,
    RiskLevel NVARCHAR(20) DEFAULT 'Low' CHECK (RiskLevel IN ('Low', 'Medium', 'High', 'Critical')),
    FOREIGN KEY (ManagerID) REFERENCES Users(UserID)
);

PRINT '✅ Projects table created (compatible with projects.py)';
GO

-- ============================================================================
-- TASKS TABLE (Compatible with tasks.py)
-- ============================================================================
CREATE TABLE Tasks (
    TaskID INT IDENTITY(1,1) PRIMARY KEY,
    ProjectID INT NOT NULL,
    Title NVARCHAR(200) NOT NULL, -- Used in tasks.py
    Description NVARCHAR(MAX),
    AssignedToID INT, -- Used in tasks.py
    Status NVARCHAR(20) DEFAULT 'To Do' CHECK (Status IN ('To Do', 'In Progress', 'Review', 'Testing', 'Done', 'Cancelled', 'Blocked')),
    Priority NVARCHAR(10) DEFAULT 'Medium' CHECK (Priority IN ('Low', 'Medium', 'High', 'Critical')),
    CreatedDate DATETIME DEFAULT GETDATE(),
    DueDate DATETIME,
    StartDate DATETIME,
    EndDate DATETIME,
    EstimatedHours DECIMAL(5,2),
    ActualHours DECIMAL(5,2),
    CompletionPercentage INT DEFAULT 0 CHECK (CompletionPercentage BETWEEN 0 AND 100),
    CreatedByID INT, -- Used in tasks.py
    UpdatedDate DATETIME DEFAULT GETDATE(),
    CompletedDate DATETIME,
    -- Additional fields from original schema
    Dependencies NVARCHAR(500), -- Comma-separated TaskIDs
    Labels NVARCHAR(500), -- Comma-separated labels
    Comments NTEXT,
    Attachments NTEXT, -- JSON string of file paths
    TaskCode NVARCHAR(20),
    StoryPoints INT DEFAULT 0,
    FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
    FOREIGN KEY (AssignedToID) REFERENCES Users(UserID),
    FOREIGN KEY (CreatedByID) REFERENCES Users(UserID)
);

PRINT '✅ Tasks table created (compatible with tasks.py)';
GO

-- ============================================================================
-- PROJECT MEMBERS TABLE
-- ============================================================================
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
GO

-- ============================================================================
-- SYSTEM SETTINGS TABLE (Compatible with settings.py)
-- ============================================================================
CREATE TABLE SystemSettings (
    SettingID INT IDENTITY(1,1) PRIMARY KEY,
    SettingKey NVARCHAR(100) UNIQUE NOT NULL,
    SettingValue NVARCHAR(MAX) NOT NULL,
    CreatedDate DATETIME DEFAULT GETDATE(),
    UpdatedDate DATETIME DEFAULT GETDATE()
);

PRINT '✅ SystemSettings table created (compatible with settings.py)';
GO

-- ============================================================================
-- ADDITIONAL TABLES FROM ORIGINAL SCHEMA
-- ============================================================================

-- Time Tracking
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

-- Comments
CREATE TABLE Comments (
    CommentID INT IDENTITY(1,1) PRIMARY KEY,
    EntityType NVARCHAR(50) NOT NULL CHECK (EntityType IN ('Project', 'Task')),
    EntityID INT NOT NULL,
    UserID INT NOT NULL,
    CommentText NTEXT NOT NULL,
    CreatedDate DATETIME DEFAULT GETDATE(),
    LastModifiedDate DATETIME DEFAULT GETDATE(),
    ParentCommentID INT,
    IsEdited BIT DEFAULT 0,
    FOREIGN KEY (UserID) REFERENCES Users(UserID),
    FOREIGN KEY (ParentCommentID) REFERENCES Comments(CommentID)
);

-- Notifications
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

-- File Attachments
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

-- Audit Log
CREATE TABLE AuditLog (
    AuditID INT IDENTITY(1,1) PRIMARY KEY,
    UserID INT,
    Action NVARCHAR(100) NOT NULL,
    EntityType NVARCHAR(50),
    EntityID INT,
    OldValues NTEXT,
    NewValues NTEXT,
    IPAddress NVARCHAR(45),
    UserAgent NVARCHAR(500),
    CreatedDate DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (UserID) REFERENCES Users(UserID)
);

PRINT '✅ Additional tables created';
GO

-- ============================================================================
-- CREATE INDEXES FOR PERFORMANCE
-- ============================================================================
PRINT '📊 Creating indexes for optimal performance...';

-- Users indexes
CREATE INDEX IX_Users_Username ON Users(Username);
CREATE INDEX IX_Users_Email ON Users(Email);
CREATE INDEX IX_Users_Role ON Users(Role);
CREATE INDEX IX_Users_IsActive ON Users(IsActive);

-- Projects indexes
CREATE INDEX IX_Projects_Status ON Projects(Status);
CREATE INDEX IX_Projects_ManagerID ON Projects(ManagerID);
CREATE INDEX IX_Projects_Priority ON Projects(Priority);
CREATE INDEX IX_Projects_CreatedDate ON Projects(CreatedDate);
CREATE INDEX IX_Projects_EndDate ON Projects(EndDate);

-- Tasks indexes
CREATE INDEX IX_Tasks_ProjectID ON Tasks(ProjectID);
CREATE INDEX IX_Tasks_AssignedToID ON Tasks(AssignedToID);
CREATE INDEX IX_Tasks_Status ON Tasks(Status);
CREATE INDEX IX_Tasks_DueDate ON Tasks(DueDate);
CREATE INDEX IX_Tasks_Priority ON Tasks(Priority);
CREATE INDEX IX_Tasks_CreatedByID ON Tasks(CreatedByID);

-- ProjectMembers indexes
CREATE INDEX IX_ProjectMembers_ProjectID ON ProjectMembers(ProjectID);
CREATE INDEX IX_ProjectMembers_UserID ON ProjectMembers(UserID);

-- Other indexes
CREATE INDEX IX_TimeTracking_TaskID_UserID ON TimeTracking(TaskID, UserID);
CREATE INDEX IX_Comments_EntityType_EntityID ON Comments(EntityType, EntityID);
CREATE INDEX IX_Notifications_UserID_IsRead ON Notifications(UserID, IsRead);
CREATE INDEX IX_AuditLog_UserID_CreatedDate ON AuditLog(UserID, CreatedDate);

PRINT '✅ All performance indexes created';
GO

-- ============================================================================
-- INSERT SYSTEM SETTINGS ONLY
-- ============================================================================
PRINT '⚙️ Inserting default system settings...';

-- Insert default system settings (compatible with settings.py)
INSERT INTO SystemSettings (SettingKey, SettingValue)
VALUES 
('app_name', '"DENSO Project Manager Pro"'),
('app_version', '"2.0.0"'),
('company_name', '"DENSO Corporation"'),
('theme', '"light"'),
('language', '"th"'),
('timezone', '"Asia/Bangkok"'),
('session_timeout', '3600'),
('max_upload_size', '100'),
('email_notifications', 'true'),
('auto_backup', 'false'),
('backup_schedule', '"02:00"'),
('backup_retention_days', '90'),
('default_currency', '"THB"'),
('working_hours_start', '"08:00"'),
('working_hours_end', '"17:00"'),
('weekend_days', '["Saturday", "Sunday"]'),
('company_logo', '"/assets/denso-logo.png"'),
('password_policy', '{"min_length": 8, "require_uppercase": true, "require_lowercase": true, "require_digits": true, "require_special": true, "history_count": 5}'),
('security_settings', '{"max_login_attempts": 5, "lockout_duration": 900, "session_cookie_secure": false, "force_password_change": false}');

PRINT '✅ System settings created';
GO

-- ============================================================================
-- CREATE VIEWS FOR COMPATIBILITY
-- ============================================================================
PRINT '👁️ Creating database views...';
GO

-- Project Overview View (compatible with analytics.py)
CREATE VIEW ProjectOverview AS
SELECT 
    p.ProjectID,
    p.Name as ProjectName,
    p.Description,
    p.Status,
    p.Priority,
    p.Budget,
    p.ActualCost,
    p.CompletionPercentage,
    p.StartDate,
    p.EndDate,
    p.ClientName,
    u.FirstName + ' ' + u.LastName as ManagerName,
    COUNT(t.TaskID) as TotalTasks,
    SUM(CASE WHEN t.Status = 'Done' THEN 1 ELSE 0 END) as CompletedTasks,
    SUM(CASE WHEN t.DueDate < GETDATE() AND t.Status != 'Done' THEN 1 ELSE 0 END) as OverdueTasks
FROM Projects p
LEFT JOIN Users u ON p.ManagerID = u.UserID
LEFT JOIN Tasks t ON p.ProjectID = t.ProjectID
GROUP BY p.ProjectID, p.Name, p.Description, p.Status, p.Priority, p.Budget, p.ActualCost, 
         p.CompletionPercentage, p.StartDate, p.EndDate, p.ClientName, u.FirstName, u.LastName;
GO

-- Task Overview View (compatible with analytics.py)
CREATE VIEW TaskOverview AS
SELECT 
    t.TaskID,
    t.Title,
    t.Description,
    t.Status,
    t.Priority,
    t.CompletionPercentage,
    t.CreatedDate,
    t.DueDate,
    t.EstimatedHours,
    t.ActualHours,
    p.Name as ProjectName,
    assigned.FirstName + ' ' + assigned.LastName as AssignedToName,
    creator.FirstName + ' ' + creator.LastName as CreatedByName,
    CASE 
        WHEN t.DueDate < GETDATE() AND t.Status != 'Done' THEN 1 
        ELSE 0 
    END as IsOverdue
FROM Tasks t
LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
LEFT JOIN Users assigned ON t.AssignedToID = assigned.UserID
LEFT JOIN Users creator ON t.CreatedByID = creator.UserID;
GO

PRINT '✅ Compatibility views created';
GO

-- ============================================================================
-- UPDATE STATISTICS
-- ============================================================================
PRINT '📈 Updating table statistics...';

UPDATE STATISTICS Users;
UPDATE STATISTICS Projects;
UPDATE STATISTICS Tasks;
UPDATE STATISTICS ProjectMembers;
UPDATE STATISTICS SystemSettings;
UPDATE STATISTICS TimeTracking;
UPDATE STATISTICS Comments;
UPDATE STATISTICS Notifications;

PRINT '✅ Statistics updated';
GO

-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================
PRINT '';
PRINT '🎉 DENSO Project Manager Pro Database Setup Complete!';
PRINT '================================================';
PRINT '✅ Database: ProjectManagerDB';
PRINT '✅ Tables: 10 production tables created';
PRINT '✅ Indexes: Performance optimized';
PRINT '✅ Views: Analytics compatible';
PRINT '✅ Settings: Default system configuration';
PRINT '';
PRINT '📝 Next Steps:';
PRINT '   1. Run insert_sample_data.sql to add your team data';
PRINT '   2. Configure your application settings';
PRINT '   3. Set up user accounts through the application';
PRINT '';
PRINT '🚀 Your DENSO Project Manager Pro database is ready!';
PRINT '================================================';

-- Final verification
SELECT 'Users' as TableName, COUNT(*) as RecordCount FROM Users
UNION ALL
SELECT 'Projects', COUNT(*) FROM Projects
UNION ALL
SELECT 'Tasks', COUNT(*) FROM Tasks
UNION ALL
SELECT 'ProjectMembers', COUNT(*) FROM ProjectMembers
UNION ALL
SELECT 'SystemSettings', COUNT(*) FROM SystemSettings
UNION ALL
SELECT 'Notifications', COUNT(*) FROM Notifications;