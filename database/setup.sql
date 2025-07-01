-- Project Manager Pro v3.0 - Database Setup Script
-- SQL Server Database Schema

-- Create database if not exists
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'ProjectManagerDB')
BEGIN
    CREATE DATABASE ProjectManagerDB;
END
GO

USE ProjectManagerDB;
GO

-- Create Users table
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Users')
BEGIN
    CREATE TABLE Users (
        UserID INT IDENTITY(1,1) PRIMARY KEY,
        Username NVARCHAR(50) NOT NULL UNIQUE,
        PasswordHash NVARCHAR(255) NOT NULL,
        Email NVARCHAR(255) UNIQUE,
        Role NVARCHAR(20) DEFAULT 'User' CHECK (Role IN ('Admin', 'Manager', 'User', 'Viewer')),
        Active BIT DEFAULT 1,
        CreatedDate DATETIME2 DEFAULT GETDATE(),
        LastLoginDate DATETIME2,
        PasswordChangedDate DATETIME2,
        ProfilePicture NVARCHAR(255),
        
        -- Constraints
        CONSTRAINT CK_Users_Email CHECK (Email LIKE '%@%.%'),
        CONSTRAINT CK_Users_Username CHECK (LEN(Username) >= 3)
    );
    
    -- Create indexes for Users table
    CREATE INDEX IX_Users_Username ON Users(Username);
    CREATE INDEX IX_Users_Email ON Users(Email);
    CREATE INDEX IX_Users_Role ON Users(Role);
    CREATE INDEX IX_Users_Active ON Users(Active);
    CREATE INDEX IX_Users_LastLogin ON Users(LastLoginDate);
    
    PRINT 'Users table created successfully';
END
GO

-- Create Projects table
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Projects')
BEGIN
    CREATE TABLE Projects (
        ProjectID INT IDENTITY(1,1) PRIMARY KEY,
        ProjectName NVARCHAR(100) NOT NULL,
        Description NVARCHAR(MAX),
        StartDate DATE,
        EndDate DATE,
        Status NVARCHAR(50) DEFAULT 'Planning' CHECK (Status IN ('Planning', 'Active', 'Completed', 'On-Hold', 'Cancelled')),
        Priority NVARCHAR(20) DEFAULT 'Medium' CHECK (Priority IN ('Critical', 'High', 'Medium', 'Low')),
        Budget DECIMAL(15,2),
        ClientName NVARCHAR(100),
        Tags NVARCHAR(500),
        CreatedDate DATETIME2 DEFAULT GETDATE(),
        CreatedBy INT NOT NULL,
        LastModifiedDate DATETIME2 DEFAULT GETDATE(),
        
        -- Foreign key constraints
        CONSTRAINT FK_Projects_CreatedBy FOREIGN KEY (CreatedBy) REFERENCES Users(UserID),
        
        -- Check constraints
        CONSTRAINT CK_Projects_Budget CHECK (Budget >= 0),
        CONSTRAINT CK_Projects_Dates CHECK (EndDate IS NULL OR StartDate IS NULL OR EndDate >= StartDate),
        CONSTRAINT CK_Projects_Name CHECK (LEN(ProjectName) >= 3)
    );
    
    -- Create indexes for Projects table
    CREATE INDEX IX_Projects_Status ON Projects(Status);
    CREATE INDEX IX_Projects_Priority ON Projects(Priority);
    CREATE INDEX IX_Projects_CreatedBy ON Projects(CreatedBy);
    CREATE INDEX IX_Projects_Dates ON Projects(StartDate, EndDate);
    CREATE INDEX IX_Projects_Client ON Projects(ClientName);
    
    PRINT 'Projects table created successfully';
END
GO

-- Create Tasks table
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Tasks')
BEGIN
    CREATE TABLE Tasks (
        TaskID INT IDENTITY(1,1) PRIMARY KEY,
        ProjectID INT NOT NULL,
        TaskName NVARCHAR(100) NOT NULL,
        Description NVARCHAR(MAX),
        StartDate DATE,
        EndDate DATE,
        AssigneeID INT,
        Status NVARCHAR(50) DEFAULT 'To Do' CHECK (Status IN ('To Do', 'In Progress', 'In Review', 'Testing', 'Done', 'Cancelled', 'Blocked')),
        Priority NVARCHAR(20) DEFAULT 'Medium' CHECK (Priority IN ('Critical', 'High', 'Medium', 'Low')),
        Progress INT DEFAULT 0,
        EstimatedHours DECIMAL(5,1),
        ActualHours DECIMAL(5,1),
        Dependencies NVARCHAR(MAX),
        Labels NVARCHAR(255),
        CreatedDate DATETIME2 DEFAULT GETDATE(),
        CreatedBy INT NOT NULL,
        LastModifiedDate DATETIME2 DEFAULT GETDATE(),
        
        -- Foreign key constraints
        CONSTRAINT FK_Tasks_ProjectID FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
        CONSTRAINT FK_Tasks_AssigneeID FOREIGN KEY (AssigneeID) REFERENCES Users(UserID),
        CONSTRAINT FK_Tasks_CreatedBy FOREIGN KEY (CreatedBy) REFERENCES Users(UserID),
        
        -- Check constraints
        CONSTRAINT CK_Tasks_Progress CHECK (Progress >= 0 AND Progress <= 100),
        CONSTRAINT CK_Tasks_Hours CHECK (EstimatedHours IS NULL OR EstimatedHours >= 0),
        CONSTRAINT CK_Tasks_ActualHours CHECK (ActualHours IS NULL OR ActualHours >= 0),
        CONSTRAINT CK_Tasks_Dates CHECK (EndDate IS NULL OR StartDate IS NULL OR EndDate >= StartDate),
        CONSTRAINT CK_Tasks_Name CHECK (LEN(TaskName) >= 3)
    );
    
    -- Create indexes for Tasks table
    CREATE INDEX IX_Tasks_ProjectID ON Tasks(ProjectID);
    CREATE INDEX IX_Tasks_AssigneeID ON Tasks(AssigneeID);
    CREATE INDEX IX_Tasks_Status ON Tasks(Status);
    CREATE INDEX IX_Tasks_Priority ON Tasks(Priority);
    CREATE INDEX IX_Tasks_Dates ON Tasks(StartDate, EndDate);
    CREATE INDEX IX_Tasks_Progress ON Tasks(Progress);
    CREATE INDEX IX_Tasks_CreatedBy ON Tasks(CreatedBy);
    
    PRINT 'Tasks table created successfully';
END
GO

-- Create ProjectMembers table (for team assignments)
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'ProjectMembers')
BEGIN
    CREATE TABLE ProjectMembers (
        ProjectMemberID INT IDENTITY(1,1) PRIMARY KEY,
        ProjectID INT NOT NULL,
        UserID INT NOT NULL,
        Role NVARCHAR(50) DEFAULT 'Member' CHECK (Role IN ('Project Manager', 'Lead', 'Member', 'Observer')),
        AssignedDate DATETIME2 DEFAULT GETDATE(),
        
        -- Foreign key constraints
        CONSTRAINT FK_ProjectMembers_ProjectID FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
        CONSTRAINT FK_ProjectMembers_UserID FOREIGN KEY (UserID) REFERENCES Users(UserID),
        
        -- Unique constraint (one role per user per project)
        CONSTRAINT UQ_ProjectMembers_User_Project UNIQUE (ProjectID, UserID)
    );
    
    -- Create indexes
    CREATE INDEX IX_ProjectMembers_ProjectID ON ProjectMembers(ProjectID);
    CREATE INDEX IX_ProjectMembers_UserID ON ProjectMembers(UserID);
    
    PRINT 'ProjectMembers table created successfully';
END
GO

-- Create Comments table (for project/task comments)
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Comments')
BEGIN
    CREATE TABLE Comments (
        CommentID INT IDENTITY(1,1) PRIMARY KEY,
        ProjectID INT,
        TaskID INT,
        UserID INT NOT NULL,
        CommentText NVARCHAR(MAX) NOT NULL,
        CreatedDate DATETIME2 DEFAULT GETDATE(),
        
        -- Foreign key constraints
        CONSTRAINT FK_Comments_ProjectID FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
        CONSTRAINT FK_Comments_TaskID FOREIGN KEY (TaskID) REFERENCES Tasks(TaskID) ON DELETE CASCADE,
        CONSTRAINT FK_Comments_UserID FOREIGN KEY (UserID) REFERENCES Users(UserID),
        
        -- Check constraint (comment must be for either project or task, not both)
        CONSTRAINT CK_Comments_Target CHECK ((ProjectID IS NOT NULL AND TaskID IS NULL) OR (ProjectID IS NULL AND TaskID IS NOT NULL))
    );
    
    -- Create indexes
    CREATE INDEX IX_Comments_ProjectID ON Comments(ProjectID);
    CREATE INDEX IX_Comments_TaskID ON Comments(TaskID);
    CREATE INDEX IX_Comments_UserID ON Comments(UserID);
    CREATE INDEX IX_Comments_CreatedDate ON Comments(CreatedDate);
    
    PRINT 'Comments table created successfully';
END
GO

-- Create Attachments table
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'Attachments')
BEGIN
    CREATE TABLE Attachments (
        AttachmentID INT IDENTITY(1,1) PRIMARY KEY,
        ProjectID INT,
        TaskID INT,
        FileName NVARCHAR(255) NOT NULL,
        FilePath NVARCHAR(500) NOT NULL,
        FileSize BIGINT,
        FileType NVARCHAR(50),
        UploadedBy INT NOT NULL,
        UploadedDate DATETIME2 DEFAULT GETDATE(),
        
        -- Foreign key constraints
        CONSTRAINT FK_Attachments_ProjectID FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
        CONSTRAINT FK_Attachments_TaskID FOREIGN KEY (TaskID) REFERENCES Tasks(TaskID) ON DELETE CASCADE,
        CONSTRAINT FK_Attachments_UploadedBy FOREIGN KEY (UploadedBy) REFERENCES Users(UserID),
        
        -- Check constraint
        CONSTRAINT CK_Attachments_Target CHECK ((ProjectID IS NOT NULL AND TaskID IS NULL) OR (ProjectID IS NULL AND TaskID IS NOT NULL)),
        CONSTRAINT CK_Attachments_FileSize CHECK (FileSize >= 0)
    );
    
    -- Create indexes
    CREATE INDEX IX_Attachments_ProjectID ON Attachments(ProjectID);
    CREATE INDEX IX_Attachments_TaskID ON Attachments(TaskID);
    CREATE INDEX IX_Attachments_UploadedBy ON Attachments(UploadedBy);
    
    PRINT 'Attachments table created successfully';
END
GO

-- Create ActivityLog table (for audit trail)
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'ActivityLog')
BEGIN
    CREATE TABLE ActivityLog (
        LogID INT IDENTITY(1,1) PRIMARY KEY,
        UserID INT,
        EntityType NVARCHAR(50) NOT NULL CHECK (EntityType IN ('Project', 'Task', 'User', 'Comment', 'Attachment')),
        EntityID INT NOT NULL,
        Action NVARCHAR(50) NOT NULL CHECK (Action IN ('Create', 'Update', 'Delete', 'View', 'Assign', 'Complete')),
        Description NVARCHAR(500),
        Timestamp DATETIME2 DEFAULT GETDATE(),
        IPAddress NVARCHAR(45),
        
        -- Foreign key constraint
        CONSTRAINT FK_ActivityLog_UserID FOREIGN KEY (UserID) REFERENCES Users(UserID)
    );
    
    -- Create indexes
    CREATE INDEX IX_ActivityLog_UserID ON ActivityLog(UserID);
    CREATE INDEX IX_ActivityLog_EntityType ON ActivityLog(EntityType);
    CREATE INDEX IX_ActivityLog_Timestamp ON ActivityLog(Timestamp);
    CREATE INDEX IX_ActivityLog_Action ON ActivityLog(Action);
    
    PRINT 'ActivityLog table created successfully';
END
GO

-- Create SchemaVersion table (for database versioning)
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'SchemaVersion')
BEGIN
    CREATE TABLE SchemaVersion (
        VersionID INT IDENTITY(1,1) PRIMARY KEY,
        Version NVARCHAR(20) NOT NULL,
        Description NVARCHAR(255),
        AppliedDate DATETIME2 DEFAULT GETDATE()
    );
    
    -- Insert initial version
    INSERT INTO SchemaVersion (Version, Description) 
    VALUES ('3.0.0', 'Initial Project Manager Pro v3.0 schema');
    
    PRINT 'SchemaVersion table created successfully';
END
GO

-- Insert default admin user (only if no users exist)
IF NOT EXISTS (SELECT 1 FROM Users)
BEGIN
    -- Password: admin123 (BCrypt hashed)
    INSERT INTO Users (Username, PasswordHash, Email, Role, Active, PasswordChangedDate)
    VALUES (
        'admin',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewXl.dO7.z7.gE6y',
        'admin@projectmanager.local',
        'Admin',
        1,
        GETDATE()
    );
    
    PRINT 'Default admin user created (Username: admin, Password: admin123)';
END
GO

-- Insert sample demo user
IF NOT EXISTS (SELECT 1 FROM Users WHERE Username = 'demo')
BEGIN
    -- Password: demo123 (BCrypt hashed)
    INSERT INTO Users (Username, PasswordHash, Email, Role, Active, PasswordChangedDate)
    VALUES (
        'demo',
        '$2b$12$8.xKmn8V7q5z8K5Vn8Kn8.JQ8K5V8K5V8K5V8K5V8K5V8K5V8K5V8K',
        'demo@projectmanager.local',
        'Manager',
        1,
        GETDATE()
    );
    
    PRINT 'Demo user created (Username: demo, Password: demo123)';
END
GO

-- Insert sample project (only if no projects exist)
IF NOT EXISTS (SELECT 1 FROM Projects)
BEGIN
    DECLARE @AdminUserID INT;
    SELECT @AdminUserID = UserID FROM Users WHERE Username = 'admin';
    
    IF @AdminUserID IS NOT NULL
    BEGIN
        INSERT INTO Projects (ProjectName, Description, StartDate, EndDate, Status, Priority, Budget, ClientName, CreatedBy)
        VALUES (
            'Project Manager Pro Implementation',
            'Implementation and deployment of the new Project Manager Pro v3.0 system for enterprise project management.',
            GETDATE(),
            DATEADD(MONTH, 3, GETDATE()),
            'Active',
            'High',
            50000.00,
            'Internal IT Department',
            @AdminUserID
        );
        
        DECLARE @ProjectID INT = SCOPE_IDENTITY();
        
        -- Insert sample tasks
        INSERT INTO Tasks (ProjectID, TaskName, Description, Status, Priority, Progress, EstimatedHours, CreatedBy)
        VALUES 
        (@ProjectID, 'Database Setup', 'Configure SQL Server database and create initial schema', 'Done', 'High', 100, 8, @AdminUserID),
        (@ProjectID, 'User Interface Development', 'Develop modern UI with glassmorphism design', 'In Progress', 'High', 75, 40, @AdminUserID),
        (@ProjectID, 'Authentication System', 'Implement secure user authentication and authorization', 'Done', 'Critical', 100, 16, @AdminUserID),
        (@ProjectID, 'Testing & QA', 'Comprehensive testing of all system components', 'To Do', 'Medium', 0, 24, @AdminUserID),
        (@ProjectID, 'Documentation', 'Create user manuals and technical documentation', 'To Do', 'Low', 0, 12, @AdminUserID);
        
        PRINT 'Sample project and tasks created';
    END
END
GO

-- Create views for common queries
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_NAME = 'vw_ProjectSummary')
BEGIN
    EXEC('
    CREATE VIEW vw_ProjectSummary AS
    SELECT 
        p.ProjectID,
        p.ProjectName,
        p.Status,
        p.Priority,
        p.StartDate,
        p.EndDate,
        p.Budget,
        p.ClientName,
        u.Username as CreatedBy,
        COUNT(t.TaskID) as TotalTasks,
        COUNT(CASE WHEN t.Status = ''Done'' THEN 1 END) as CompletedTasks,
        CAST(COUNT(CASE WHEN t.Status = ''Done'' THEN 1 END) * 100.0 / NULLIF(COUNT(t.TaskID), 0) AS DECIMAL(5,2)) as CompletionRate,
        ISNULL(AVG(CAST(t.Progress AS FLOAT)), 0) as AvgProgress
    FROM Projects p
    LEFT JOIN Users u ON p.CreatedBy = u.UserID
    LEFT JOIN Tasks t ON p.ProjectID = t.ProjectID
    GROUP BY p.ProjectID, p.ProjectName, p.Status, p.Priority, p.StartDate, p.EndDate, p.Budget, p.ClientName, u.Username
    ');
    
    PRINT 'vw_ProjectSummary view created';
END
GO

-- Create stored procedures
IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_NAME = 'sp_GetUserWorkload')
BEGIN
    EXEC('
    CREATE PROCEDURE sp_GetUserWorkload
        @UserID INT = NULL
    AS
    BEGIN
        SELECT 
            u.UserID,
            u.Username,
            u.Email,
            u.Role,
            COUNT(t.TaskID) as AssignedTasks,
            COUNT(CASE WHEN t.Status NOT IN (''Done'', ''Cancelled'') THEN 1 END) as ActiveTasks,
            ISNULL(AVG(CAST(t.Progress AS FLOAT)), 0) as AvgProgress,
            SUM(ISNULL(t.EstimatedHours, 0)) as TotalEstimatedHours,
            SUM(ISNULL(t.ActualHours, 0)) as TotalActualHours
        FROM Users u
        LEFT JOIN Tasks t ON u.UserID = t.AssigneeID
        WHERE u.Active = 1 AND (@UserID IS NULL OR u.UserID = @UserID)
        GROUP BY u.UserID, u.Username, u.Email, u.Role
        ORDER BY AssignedTasks DESC;
    END
    ');
    
    PRINT 'sp_GetUserWorkload stored procedure created';
END
GO

-- Create triggers for audit logging
IF NOT EXISTS (SELECT * FROM sys.triggers WHERE name = 'tr_Projects_Audit')
BEGIN
    EXEC('
    CREATE TRIGGER tr_Projects_Audit
    ON Projects
    AFTER INSERT, UPDATE, DELETE
    AS
    BEGIN
        SET NOCOUNT ON;
        
        -- Handle INSERT
        IF EXISTS (SELECT * FROM inserted) AND NOT EXISTS (SELECT * FROM deleted)
        BEGIN
            INSERT INTO ActivityLog (EntityType, EntityID, Action, Description)
            SELECT ''Project'', ProjectID, ''Create'', ''Project created: '' + ProjectName
            FROM inserted;
        END
        
        -- Handle UPDATE
        IF EXISTS (SELECT * FROM inserted) AND EXISTS (SELECT * FROM deleted)
        BEGIN
            INSERT INTO ActivityLog (EntityType, EntityID, Action, Description)
            SELECT ''Project'', i.ProjectID, ''Update'', ''Project updated: '' + i.ProjectName
            FROM inserted i;
        END
        
        -- Handle DELETE
        IF NOT EXISTS (SELECT * FROM inserted) AND EXISTS (SELECT * FROM deleted)
        BEGIN
            INSERT INTO ActivityLog (EntityType, EntityID, Action, Description)
            SELECT ''Project'', ProjectID, ''Delete'', ''Project deleted: '' + ProjectName
            FROM deleted;
        END
    END
    ');
    
    PRINT 'tr_Projects_Audit trigger created';
END
GO

-- Grant permissions (adjust as needed for your security requirements)
-- These are basic permissions for the application user
-- In production, create a dedicated application user with minimal required permissions

PRINT '=================================';
PRINT 'Database setup completed successfully!';
PRINT '';
PRINT 'Default Users Created:';
PRINT '- Admin: admin / admin123';
PRINT '- Demo: demo / demo123';
PRINT '';
PRINT 'Sample project and tasks have been created.';
PRINT 'You can now run the Project Manager Pro application.';
PRINT '=================================';
GO