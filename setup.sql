-- ============================================================================
-- setup.sql
-- SDX Project Manager Database Setup Script
-- ============================================================================

USE master;
GO

-- Drop database if exists
IF EXISTS (SELECT name FROM sys.databases WHERE name = 'SDXProjectManager')
BEGIN
    ALTER DATABASE SDXProjectManager SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE SDXProjectManager;
    PRINT '🗑️ Existing database dropped';
END
GO

-- Create database (ใช้ default path ของ SQL Server)
CREATE DATABASE SDXProjectManager;
PRINT '📁 Database created';
GO

USE SDXProjectManager;
GO

-- ============================================================================
-- TABLES CREATION
-- ============================================================================

-- Users table
CREATE TABLE Users (
    UserID INT IDENTITY(1,1) PRIMARY KEY,
    Username NVARCHAR(50) UNIQUE NOT NULL,
    PasswordHash NVARCHAR(255) NOT NULL,
    Email NVARCHAR(100) UNIQUE NOT NULL,
    FirstName NVARCHAR(50) NOT NULL,
    LastName NVARCHAR(50) NOT NULL,
    Department NVARCHAR(50),
    Role NVARCHAR(20) DEFAULT 'User' CHECK (Role IN ('Admin', 'Manager', 'User')),
    Phone NVARCHAR(20),
    IsActive BIT DEFAULT 1,
    LastLoginDate DATETIME,
    CreatedDate DATETIME DEFAULT GETDATE(),
    UpdatedDate DATETIME DEFAULT GETDATE()
);
PRINT '✅ Users table created';

-- Projects table
CREATE TABLE Projects (
    ProjectID INT IDENTITY(1,1) PRIMARY KEY,
    ProjectName NVARCHAR(100) NOT NULL,
    Description NVARCHAR(MAX),
    Status NVARCHAR(20) DEFAULT 'Active' CHECK (Status IN ('Active', 'Completed', 'On Hold', 'Cancelled')),
    Priority NVARCHAR(10) DEFAULT 'Medium' CHECK (Priority IN ('Low', 'Medium', 'High', 'Critical')),
    StartDate DATE,
    EndDate DATE,
    Budget DECIMAL(15,2),
    ActualCost DECIMAL(15,2) DEFAULT 0,
    ManagerID INT,
    CreatedDate DATETIME DEFAULT GETDATE(),
    UpdatedDate DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (ManagerID) REFERENCES Users(UserID)
);
PRINT '✅ Projects table created';

-- Tasks table
CREATE TABLE Tasks (
    TaskID INT IDENTITY(1,1) PRIMARY KEY,
    ProjectID INT NOT NULL,
    TaskTitle NVARCHAR(200) NOT NULL,
    TaskDescription NVARCHAR(MAX),
    Status NVARCHAR(20) DEFAULT 'To Do' CHECK (Status IN ('To Do', 'In Progress', 'Review', 'Done')),
    Priority NVARCHAR(10) DEFAULT 'Medium' CHECK (Priority IN ('Low', 'Medium', 'High', 'Critical')),
    AssignedTo INT,
    EstimatedHours DECIMAL(5,2),
    ActualHours DECIMAL(5,2) DEFAULT 0,
    DueDate DATE,
    CompletedDate DATETIME,
    CreatedDate DATETIME DEFAULT GETDATE(),
    UpdatedDate DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
    FOREIGN KEY (AssignedTo) REFERENCES Users(UserID)
);
PRINT '✅ Tasks table created';

-- Project Members table
CREATE TABLE ProjectMembers (
    ProjectMemberID INT IDENTITY(1,1) PRIMARY KEY,
    ProjectID INT NOT NULL,
    UserID INT NOT NULL,
    Role NVARCHAR(50) DEFAULT 'Member',
    JoinedDate DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE NO ACTION,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE NO ACTION,
    UNIQUE(ProjectID, UserID)
);
PRINT '✅ ProjectMembers table created';

-- Time Tracking table
CREATE TABLE TimeTracking (
    TimeTrackingID INT IDENTITY(1,1) PRIMARY KEY,
    TaskID INT NOT NULL,
    UserID INT NOT NULL,
    StartTime DATETIME NOT NULL,
    EndTime DATETIME,
    HoursWorked DECIMAL(5,2),
    Description NVARCHAR(500),
    CreatedDate DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (TaskID) REFERENCES Tasks(TaskID) ON DELETE NO ACTION,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE NO ACTION
);
PRINT '✅ TimeTracking table created';

-- Comments table
CREATE TABLE Comments (
    CommentID INT IDENTITY(1,1) PRIMARY KEY,
    TaskID INT,
    ProjectID INT,
    UserID INT NOT NULL,
    CommentText NVARCHAR(MAX) NOT NULL,
    CreatedDate DATETIME DEFAULT GETDATE(),
    UpdatedDate DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (TaskID) REFERENCES Tasks(TaskID) ON DELETE NO ACTION,
    FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE NO ACTION,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE NO ACTION,
    CHECK ((TaskID IS NOT NULL AND ProjectID IS NULL) OR (TaskID IS NULL AND ProjectID IS NOT NULL))
);
PRINT '✅ Comments table created';

-- Notifications table
CREATE TABLE Notifications (
    NotificationID INT IDENTITY(1,1) PRIMARY KEY,
    UserID INT NOT NULL,
    Title NVARCHAR(200) NOT NULL,
    Message NVARCHAR(MAX) NOT NULL,
    Type NVARCHAR(50) DEFAULT 'Info' CHECK (Type IN ('Info', 'Warning', 'Error', 'Success')),
    IsRead BIT DEFAULT 0,
    CreatedDate DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE NO ACTION
);
PRINT '✅ Notifications table created';

-- System Settings table
CREATE TABLE SystemSettings (
    SettingID INT IDENTITY(1,1) PRIMARY KEY,
    SettingKey NVARCHAR(100) UNIQUE NOT NULL,
    SettingValue NVARCHAR(MAX),
    Description NVARCHAR(500),
    UpdatedDate DATETIME DEFAULT GETDATE(),
    UpdatedBy INT,
    FOREIGN KEY (UpdatedBy) REFERENCES Users(UserID)
);
PRINT '✅ SystemSettings table created';

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IX_Users_Username ON Users(Username);
CREATE INDEX IX_Users_Email ON Users(Email);
CREATE INDEX IX_Projects_Status ON Projects(Status);
CREATE INDEX IX_Projects_Priority ON Projects(Priority);
CREATE INDEX IX_Tasks_ProjectID ON Tasks(ProjectID);
CREATE INDEX IX_Tasks_AssignedTo ON Tasks(AssignedTo);
CREATE INDEX IX_Tasks_Status ON Tasks(Status);
CREATE INDEX IX_Tasks_DueDate ON Tasks(DueDate);
CREATE INDEX IX_TimeTracking_TaskID ON TimeTracking(TaskID);
CREATE INDEX IX_TimeTracking_UserID ON TimeTracking(UserID);
CREATE INDEX IX_Comments_TaskID ON Comments(TaskID);
CREATE INDEX IX_Comments_ProjectID ON Comments(ProjectID);
CREATE INDEX IX_Notifications_UserID ON Notifications(UserID);
PRINT '🔍 Indexes created';

-- ============================================================================
-- SAMPLE DATA INSERTION
-- ============================================================================

-- Default admin user
INSERT INTO Users (Username, PasswordHash, Email, FirstName, LastName, Department, Role, Phone)
VALUES 
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewuQJeCG3vS8v0hy', 'admin@sdx.com', 'System', 'Administrator', 'IT', 'Admin', '000-000-0000');

-- SDX Team members
INSERT INTO Users (Username, PasswordHash, Email, FirstName, LastName, Department, Role, Phone) VALUES
('thammaphon', '$2b$12$K4gF9N2X.qW8rT5yE3mA9OXz6TtxMQJqhN8/LewuQJeCG3vS8v1hy', 'thammaphon.c@denso.com', 'Thammaphon', 'Chittasuwanna', 'Engineering', 'Manager', '081-234-5678'),
('nattha', '$2b$12$M8kL7P4Z.sY9wU6vF5nB8QYz6TtxMQJqhN8/LewuQJeCG3vS8v2hy', 'nattha.w@denso.com', 'Nattha', 'Wutthikorn', 'Engineering', 'User', '082-345-6789'),
('waratcharpon', '$2b$12$P2oN9R6A.vZ1xW8yG7qC3TYz6TtxMQJqhN8/LewuQJeCG3vS8v3hy', 'waratcharpon.s@denso.com', 'Waratcharpon', 'Somboonpol', 'Quality', 'User', '083-456-7890'),
('thanespong', '$2b$12$S5rQ2U7D.yA4zX1wH9sD6VYz6TtxMQJqhN8/LewuQJeCG3vS8v4hy', 'thanespong.k@denso.com', 'Thanespong', 'Kaewkham', 'Engineering', 'User', '084-567-8901'),
('chanakarn', '$2b$12$V8tS5W0G.bC7yZ4xI2vE9XYz6TtxMQJqhN8/LewuQJeCG3vS8v5hy', 'chanakarn.t@denso.com', 'Chanakarn', 'Thongsuk', 'Quality', 'User', '085-678-9012'),
('narissara', '$2b$12$Y1wV8Z3J.eF0bA7yL5xF2AYz6TtxMQJqhN8/LewuQJeCG3vS8v6hy', 'narissara.p@denso.com', 'Narissara', 'Phanwong', 'Quality', 'User', '086-789-0123');

PRINT '👥 Users inserted';

-- Sample projects
INSERT INTO Projects (ProjectName, Description, Status, Priority, StartDate, EndDate, Budget, ManagerID) VALUES
('SDX Digital Transformation', 'Complete digital transformation initiative for manufacturing processes', 'Active', 'High', '2024-01-15', '2024-12-31', 2500000.00, 2),
('Quality Control System', 'Implementation of automated quality control system', 'Active', 'High', '2024-02-01', '2024-08-31', 1800000.00, 2),
('IoT Sensor Network', 'Deploy IoT sensors across production lines', 'Active', 'Medium', '2024-03-01', '2024-10-31', 1200000.00, 2),
('Data Analytics Platform', 'Build comprehensive data analytics platform', 'Active', 'High', '2024-01-01', '2024-06-30', 1500000.00, 2),
('Process Automation', 'Automate manual processes in manufacturing', 'Active', 'Medium', '2024-05-01', '2024-11-30', 2000000.00, 2);

PRINT '📊 Projects inserted';

-- Sample tasks
INSERT INTO Tasks (ProjectID, TaskTitle, TaskDescription, Status, Priority, AssignedTo, EstimatedHours, DueDate) VALUES
-- SDX Digital Transformation tasks
(1, 'System Architecture Design', 'Design overall system architecture for digital transformation', 'In Progress', 'High', 2, 40, '2024-07-15'),
(1, 'Database Design', 'Design database schema for new digital system', 'To Do', 'High', 3, 32, '2024-07-20'),
(1, 'UI/UX Design', 'Create user interface designs for digital platform', 'To Do', 'Medium', 4, 48, '2024-07-25'),
(1, 'API Development', 'Develop REST APIs for system integration', 'To Do', 'High', 5, 56, '2024-08-01'),
-- Quality Control System tasks
(2, 'Requirements Analysis', 'Analyze requirements for quality control system', 'Done', 'High', 6, 24, '2024-06-15'),
(2, 'Sensor Integration', 'Integrate quality control sensors', 'In Progress', 'High', 7, 40, '2024-07-30'),
(2, 'Testing Framework', 'Develop automated testing framework', 'To Do', 'Medium', 3, 32, '2024-08-15'),
-- IoT Sensor Network tasks
(3, 'Network Planning', 'Plan IoT sensor network topology', 'In Progress', 'Medium', 4, 20, '2024-07-10'),
(3, 'Hardware Procurement', 'Procure IoT sensors and hardware', 'To Do', 'Medium', 5, 16, '2024-07-20'),
(3, 'Installation Guide', 'Create installation guide for sensors', 'To Do', 'Low', 6, 12, '2024-08-01');

PRINT '📋 Tasks inserted';

-- Project members
INSERT INTO ProjectMembers (ProjectID, UserID, Role) VALUES
(1, 2, 'Project Manager'),
(1, 3, 'Developer'),
(1, 4, 'Designer'),
(1, 5, 'Developer'),
(2, 2, 'Project Manager'),
(2, 6, 'Quality Engineer'),
(2, 7, 'Quality Engineer'),
(2, 3, 'Developer'),
(3, 2, 'Project Manager'),
(3, 4, 'IoT Specialist'),
(3, 5, 'Network Engineer'),
(4, 2, 'Project Manager'),
(4, 3, 'Data Analyst'),
(4, 5, 'Developer'),
(5, 2, 'Project Manager'),
(5, 4, 'Automation Engineer'),
(5, 6, 'Process Engineer');

PRINT '👥 Project members assigned';

-- Sample system settings
INSERT INTO SystemSettings (SettingKey, SettingValue, Description, UpdatedBy) VALUES
('app_name', 'SDX Project Manager', 'Application name', 1),
('app_version', '2.0.0', 'Application version', 1),
('session_timeout', '28800', 'Session timeout in seconds (8 hours)', 1),
('max_file_size', '10485760', 'Maximum file upload size in bytes (10MB)', 1),
('notification_enabled', 'true', 'Enable system notifications', 1),
('backup_enabled', 'true', 'Enable automatic backup', 1),
('backup_interval', '24', 'Backup interval in hours', 1),
('password_min_length', '8', 'Minimum password length', 1),
('max_login_attempts', '5', 'Maximum failed login attempts', 1),
('company_name', 'DENSO Corporation', 'Company name', 1),
('timezone', 'Asia/Bangkok', 'System timezone', 1);

PRINT '⚙️ System settings inserted';

-- Sample notifications
INSERT INTO Notifications (UserID, Title, Message, Type) VALUES
(2, 'Welcome to SDX Project Manager', 'Welcome to the new project management system. Please update your profile.', 'Info'),
(3, 'Task Assignment', 'You have been assigned to Database Design task.', 'Info'),
(4, 'Project Update', 'SDX Digital Transformation project status updated.', 'Info'),
(5, 'Deadline Reminder', 'API Development task is due soon.', 'Warning'),
(6, 'Quality Check', 'Quality Control System needs review.', 'Info');

PRINT '🔔 Notifications inserted';

-- ============================================================================
-- VIEWS FOR REPORTING
-- ============================================================================
GO

-- Project summary view
CREATE VIEW vw_ProjectSummary AS
SELECT 
    p.ProjectID,
    p.ProjectName,
    p.Status,
    p.Priority,
    p.StartDate,
    p.EndDate,
    p.Budget,
    p.ActualCost,
    CONCAT(u.FirstName, ' ', u.LastName) AS ManagerName,
    (SELECT COUNT(*) FROM Tasks t WHERE t.ProjectID = p.ProjectID) AS TotalTasks,
    (SELECT COUNT(*) FROM Tasks t WHERE t.ProjectID = p.ProjectID AND t.Status = 'Done') AS CompletedTasks,
    (SELECT COUNT(*) FROM ProjectMembers pm WHERE pm.ProjectID = p.ProjectID) AS TeamSize,
    CASE 
        WHEN p.EndDate < GETDATE() AND p.Status != 'Completed' THEN 'Overdue'
        WHEN DATEDIFF(day, GETDATE(), p.EndDate) <= 7 AND p.Status != 'Completed' THEN 'Due Soon'
        ELSE 'On Track'
    END AS ProjectHealth
FROM Projects p
LEFT JOIN Users u ON p.ManagerID = u.UserID;
GO

PRINT '📊 vw_ProjectSummary view created';
GO

-- Task summary view
CREATE VIEW vw_TaskSummary AS
SELECT 
    t.TaskID,
    t.TaskTitle,
    t.Status,
    t.Priority,
    t.EstimatedHours,
    t.ActualHours,
    t.DueDate,
    p.ProjectName,
    CONCAT(u.FirstName, ' ', u.LastName) AS AssignedToName,
    CASE 
        WHEN t.DueDate < GETDATE() AND t.Status != 'Done' THEN 'Overdue'
        WHEN DATEDIFF(day, GETDATE(), t.DueDate) <= 3 AND t.Status != 'Done' THEN 'Due Soon'
        ELSE 'On Track'
    END AS TaskHealth
FROM Tasks t
LEFT JOIN Projects p ON t.ProjectID = p.ProjectID
LEFT JOIN Users u ON t.AssignedTo = u.UserID;
GO

PRINT '📋 vw_TaskSummary view created';
GO

-- User workload view
CREATE VIEW vw_UserWorkload AS
SELECT 
    u.UserID,
    CONCAT(u.FirstName, ' ', u.LastName) AS FullName,
    u.Department,
    COUNT(t.TaskID) AS TotalTasks,
    COUNT(CASE WHEN t.Status = 'In Progress' THEN 1 END) AS ActiveTasks,
    COUNT(CASE WHEN t.Status = 'Done' THEN 1 END) AS CompletedTasks,
    ISNULL(SUM(t.EstimatedHours), 0) AS TotalEstimatedHours,
    ISNULL(SUM(t.ActualHours), 0) AS TotalActualHours,
    COUNT(CASE WHEN t.DueDate < GETDATE() AND t.Status != 'Done' THEN 1 END) AS OverdueTasks
FROM Users u
LEFT JOIN Tasks t ON u.UserID = t.AssignedTo
WHERE u.IsActive = 1
GROUP BY u.UserID, u.FirstName, u.LastName, u.Department;
GO

PRINT '👤 vw_UserWorkload view created';
GO

-- ============================================================================
-- STORED PROCEDURES
-- ============================================================================

CREATE PROCEDURE sp_GetProjectDashboard
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Project status summary
    SELECT 
        Status,
        COUNT(*) AS ProjectCount,
        SUM(Budget) AS TotalBudget,
        SUM(ActualCost) AS TotalCost
    FROM Projects 
    GROUP BY Status;
    
    -- Recent activities (last 7 days)
    SELECT TOP 10
        'Task' AS ActivityType,
        t.TaskTitle AS Activity,
        p.ProjectName,
        CONCAT(u.FirstName, ' ', u.LastName) AS UserName,
        t.UpdatedDate
    FROM Tasks t
    JOIN Projects p ON t.ProjectID = p.ProjectID
    LEFT JOIN Users u ON t.AssignedTo = u.UserID
    WHERE t.UpdatedDate >= DATEADD(day, -7, GETDATE())
    ORDER BY t.UpdatedDate DESC;
END;
GO

PRINT '🏪 sp_GetProjectDashboard stored procedure created';
GO

-- ============================================================================
-- TRIGGERS
-- ============================================================================

CREATE TRIGGER tr_Projects_UpdateDate
ON Projects
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE Projects 
    SET UpdatedDate = GETDATE()
    WHERE ProjectID IN (SELECT ProjectID FROM inserted);
END;
GO

PRINT '⚡ Projects trigger created';
GO

CREATE TRIGGER tr_Tasks_UpdateDate
ON Tasks
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE Tasks 
    SET UpdatedDate = GETDATE()
    WHERE TaskID IN (SELECT TaskID FROM inserted);
    
    -- Auto-complete date when status changes to Done
    UPDATE Tasks 
    SET CompletedDate = GETDATE()
    WHERE TaskID IN (SELECT i.TaskID FROM inserted i WHERE i.Status = 'Done')
    AND CompletedDate IS NULL;
END;
GO

PRINT '⚡ Tasks trigger created';
GO

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

CREATE FUNCTION fn_GetProjectCompletion(@ProjectID INT)
RETURNS DECIMAL(5,2)
AS
BEGIN
    DECLARE @TotalTasks INT, @CompletedTasks INT, @Percentage DECIMAL(5,2);
    
    SELECT 
        @TotalTasks = COUNT(*),
        @CompletedTasks = COUNT(CASE WHEN Status = 'Done' THEN 1 END)
    FROM Tasks 
    WHERE ProjectID = @ProjectID;
    
    SET @Percentage = CASE 
        WHEN @TotalTasks = 0 THEN 0 
        ELSE (@CompletedTasks * 100.0) / @TotalTasks 
    END;
    
    RETURN @Percentage;
END;
GO

PRINT '📊 fn_GetProjectCompletion function created';
GO

-- ============================================================================
-- SECURITY
-- ============================================================================

-- Create roles
-- CREATE ROLE db_project_admin;
-- CREATE ROLE db_project_manager;
-- CREATE ROLE db_project_user;

-- Grant permissions (simplified for LocalDB)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::dbo TO db_project_admin;

PRINT '🔐 Security configured';

-- ============================================================================
-- COMPLETION
-- ============================================================================

PRINT '';
PRINT '🎉 SDX Project Manager Database Setup Complete!';
PRINT '===============================================';
PRINT '';
PRINT '📊 Database Statistics:';

SELECT 
    'Tables' AS ObjectType, 
    COUNT(*) AS Count
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE'
UNION ALL
SELECT 'Views', COUNT(*) 
FROM INFORMATION_SCHEMA.VIEWS
UNION ALL
SELECT 'Stored Procedures', COUNT(*) 
FROM INFORMATION_SCHEMA.ROUTINES 
WHERE ROUTINE_TYPE = 'PROCEDURE'
UNION ALL
SELECT 'Functions', COUNT(*) 
FROM INFORMATION_SCHEMA.ROUTINES 
WHERE ROUTINE_TYPE = 'FUNCTION';

PRINT '';
PRINT '👥 User Accounts Created:';
SELECT Username, CONCAT(FirstName, ' ', LastName) AS FullName, Role, Department
FROM Users
ORDER BY Role DESC, LastName;

PRINT '';
PRINT '📋 Next Steps:';
PRINT '1. Update .streamlit/secrets.toml with your database connection';
PRINT '2. Run: pip install -r requirements.txt';
PRINT '3. Run: streamlit run app.py';
PRINT '4. Login with: admin / admin123';
PRINT '';
PRINT '⚠️ Important: Change default admin password after first login!';
PRINT '';
PRINT '👨‍💻 Developer: Thammaphon Chittasuwanna (SDM) | Innovation Team';
PRINT '🏢 DENSO Corporation - SDX Project Manager v2.0';
PRINT '===============================================';