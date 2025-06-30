-- 🚀 Project Manager Pro v3.0 - Database Setup Script
-- Complete database schema with enhanced features and security

-- Create database if it doesn't exist
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'ProjectManagerPro')
BEGIN
    CREATE DATABASE ProjectManagerPro;
    PRINT 'Database ProjectManagerPro created successfully';
END
GO

USE ProjectManagerPro;
GO

-- Enable advanced features
EXEC sp_configure 'show advanced options', 1;
RECONFIGURE;
GO

-- ============================================================================
-- TABLES CREATION
-- ============================================================================

-- Users table with comprehensive user management
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
BEGIN
    CREATE TABLE Users (
        UserID INT IDENTITY(1,1) PRIMARY KEY,
        Username NVARCHAR(50) NOT NULL UNIQUE,
        PasswordHash NVARCHAR(255) NOT NULL,
        Email NVARCHAR(255) UNIQUE,
        FirstName NVARCHAR(50),
        LastName NVARCHAR(50),
        Role NVARCHAR(20) DEFAULT 'User' CHECK (Role IN ('Admin', 'Manager', 'User')),
        Active BIT DEFAULT 1,
        CreatedDate DATETIME2 DEFAULT GETDATE(),
        LastLoginDate DATETIME2,
        PasswordChangedDate DATETIME2 DEFAULT GETDATE(),
        ProfilePicture NVARCHAR(255),
        Phone NVARCHAR(20),
        Department NVARCHAR(50),
        JobTitle NVARCHAR(100),
        FailedLoginAttempts INT DEFAULT 0,
        LockedUntil DATETIME2,
        LastModifiedDate DATETIME2 DEFAULT GETDATE(),
        LastModifiedBy INT,
        Timezone NVARCHAR(50) DEFAULT 'UTC',
        Language NVARCHAR(10) DEFAULT 'en',
        NotificationPreferences NVARCHAR(MAX), -- JSON format
        TwoFactorEnabled BIT DEFAULT 0,
        TwoFactorSecret NVARCHAR(255)
    );
    
    PRINT 'Users table created successfully';
END
GO

-- Projects table with enhanced project management features
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Projects' AND xtype='U')
BEGIN
    CREATE TABLE Projects (
        ProjectID INT IDENTITY(1,1) PRIMARY KEY,
        ProjectName NVARCHAR(100) NOT NULL,
        Description NVARCHAR(MAX),
        StartDate DATE,
        EndDate DATE,
        Status NVARCHAR(50) DEFAULT 'Planning' CHECK (Status IN ('Planning', 'Active', 'On Hold', 'Completed', 'Cancelled')),
        Priority NVARCHAR(20) DEFAULT 'Medium' CHECK (Priority IN ('Low', 'Medium', 'High', 'Critical')),
        Budget DECIMAL(15,2),
        ActualCost DECIMAL(15,2) DEFAULT 0,
        ClientName NVARCHAR(100),
        ClientEmail NVARCHAR(255),
        ClientPhone NVARCHAR(20),
        Tags NVARCHAR(500),
        Progress INT DEFAULT 0 CHECK (Progress >= 0 AND Progress <= 100),
        EstimatedHours DECIMAL(8,2),
        ActualHours DECIMAL(8,2) DEFAULT 0,
        CreatedDate DATETIME2 DEFAULT GETDATE(),
        CreatedBy INT NOT NULL,
        LastModifiedDate DATETIME2 DEFAULT GETDATE(),
        LastModifiedBy INT,
        CompletedDate DATETIME2,
        IsTemplate BIT DEFAULT 0,
        TemplateID INT,
        Color NVARCHAR(7) DEFAULT '#667eea',
        Risk NVARCHAR(20) DEFAULT 'Low' CHECK (Risk IN ('Low', 'Medium', 'High')),
        Category NVARCHAR(50),
        BusinessValue NVARCHAR(20) DEFAULT 'Medium' CHECK (BusinessValue IN ('Low', 'Medium', 'High')),
        Methodology NVARCHAR(50) DEFAULT 'Agile',
        CONSTRAINT FK_Projects_CreatedBy FOREIGN KEY (CreatedBy) REFERENCES Users(UserID),
        CONSTRAINT FK_Projects_LastModifiedBy FOREIGN KEY (LastModifiedBy) REFERENCES Users(UserID),
        CONSTRAINT FK_Projects_Template FOREIGN KEY (TemplateID) REFERENCES Projects(ProjectID)
    );
    
    PRINT 'Projects table created successfully';
END
GO

-- Tasks table with comprehensive task management
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Tasks' AND xtype='U')
BEGIN
    CREATE TABLE Tasks (
        TaskID INT IDENTITY(1,1) PRIMARY KEY,
        ProjectID INT NOT NULL,
        TaskName NVARCHAR(100) NOT NULL,
        Description NVARCHAR(MAX),
        StartDate DATE,
        EndDate DATE,
        DueDate DATE,
        AssigneeID INT,
        Status NVARCHAR(50) DEFAULT 'To Do' CHECK (Status IN ('To Do', 'In Progress', 'Review', 'Testing', 'Completed', 'Cancelled')),
        Priority NVARCHAR(20) DEFAULT 'Medium' CHECK (Priority IN ('Low', 'Medium', 'High', 'Critical')),
        Progress INT DEFAULT 0 CHECK (Progress >= 0 AND Progress <= 100),
        EstimatedHours DECIMAL(5,1),
        ActualHours DECIMAL(5,1) DEFAULT 0,
        Dependencies NVARCHAR(MAX), -- Comma-separated TaskIDs
        Labels NVARCHAR(255),
        ParentTaskID INT,
        Order_Index INT DEFAULT 0,
        CreatedDate DATETIME2 DEFAULT GETDATE(),
        CreatedBy INT NOT NULL,
        LastModifiedDate DATETIME2 DEFAULT GETDATE(),
        LastModifiedBy INT,
        CompletedDate DATETIME2,
        IsRecurring BIT DEFAULT 0,
        RecurrencePattern NVARCHAR(100),
        StoryPoints INT,
        Complexity NVARCHAR(20) DEFAULT 'Medium' CHECK (Complexity IN ('Low', 'Medium', 'High')),
        TaskType NVARCHAR(50) DEFAULT 'Task',
        BlockedReason NVARCHAR(500),
        CONSTRAINT FK_Tasks_Project FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
        CONSTRAINT FK_Tasks_Assignee FOREIGN KEY (AssigneeID) REFERENCES Users(UserID),
        CONSTRAINT FK_Tasks_CreatedBy FOREIGN KEY (CreatedBy) REFERENCES Users(UserID),
        CONSTRAINT FK_Tasks_LastModifiedBy FOREIGN KEY (LastModifiedBy) REFERENCES Users(UserID),
        CONSTRAINT FK_Tasks_Parent FOREIGN KEY (ParentTaskID) REFERENCES Tasks(TaskID)
    );
    
    PRINT 'Tasks table created successfully';
END
GO

-- Project Members table for team management
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ProjectMembers' AND xtype='U')
BEGIN
    CREATE TABLE ProjectMembers (
        ProjectMemberID INT IDENTITY(1,1) PRIMARY KEY,
        ProjectID INT NOT NULL,
        UserID INT NOT NULL,
        Role NVARCHAR(50) DEFAULT 'Member' CHECK (Role IN ('Owner', 'Manager', 'Member', 'Observer')),
        JoinedDate DATETIME2 DEFAULT GETDATE(),
        LeftDate DATETIME2,
        IsActive BIT DEFAULT 1,
        Permissions NVARCHAR(MAX), -- JSON format for granular permissions
        HourlyRate DECIMAL(8,2),
        CONSTRAINT FK_ProjectMembers_Project FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
        CONSTRAINT FK_ProjectMembers_User FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE,
        CONSTRAINT UK_ProjectMembers_Unique UNIQUE(ProjectID, UserID)
    );
    
    PRINT 'ProjectMembers table created successfully';
END
GO

-- Comments table for collaboration
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Comments' AND xtype='U')
BEGIN
    CREATE TABLE Comments (
        CommentID INT IDENTITY(1,1) PRIMARY KEY,
        ProjectID INT,
        TaskID INT,
        UserID INT NOT NULL,
        Comment NVARCHAR(MAX) NOT NULL,
        CommentType NVARCHAR(20) DEFAULT 'General' CHECK (CommentType IN ('General', 'Update', 'Issue', 'Question')),
        CreatedDate DATETIME2 DEFAULT GETDATE(),
        LastModifiedDate DATETIME2,
        LastModifiedBy INT,
        IsDeleted BIT DEFAULT 0,
        ParentCommentID INT,
        Mentions NVARCHAR(MAX), -- JSON array of mentioned user IDs
        Attachments NVARCHAR(MAX), -- JSON array of attachment references
        CONSTRAINT FK_Comments_Project FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
        CONSTRAINT FK_Comments_Task FOREIGN KEY (TaskID) REFERENCES Tasks(TaskID) ON DELETE CASCADE,
        CONSTRAINT FK_Comments_User FOREIGN KEY (UserID) REFERENCES Users(UserID),
        CONSTRAINT FK_Comments_LastModifiedBy FOREIGN KEY (LastModifiedBy) REFERENCES Users(UserID),
        CONSTRAINT FK_Comments_Parent FOREIGN KEY (ParentCommentID) REFERENCES Comments(CommentID),
        CONSTRAINT CK_Comments_Reference CHECK (ProjectID IS NOT NULL OR TaskID IS NOT NULL)
    );
    
    PRINT 'Comments table created successfully';
END
GO

-- Time Logs table for time tracking
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='TimeLogs' AND xtype='U')
BEGIN
    CREATE TABLE TimeLogs (
        TimeLogID INT IDENTITY(1,1) PRIMARY KEY,
        TaskID INT NOT NULL,
        UserID INT NOT NULL,
        StartTime DATETIME2 NOT NULL,
        EndTime DATETIME2,
        Duration DECIMAL(5,2), -- In hours
        Description NVARCHAR(500),
        LogDate DATE DEFAULT CAST(GETDATE() AS DATE),
        CreatedDate DATETIME2 DEFAULT GETDATE(),
        LastModifiedDate DATETIME2 DEFAULT GETDATE(),
        IsBillable BIT DEFAULT 1,
        HourlyRate DECIMAL(8,2),
        Status NVARCHAR(20) DEFAULT 'Active' CHECK (Status IN ('Active', 'Paused', 'Completed')),
        ApprovedBy INT,
        ApprovedDate DATETIME2,
        CONSTRAINT FK_TimeLogs_Task FOREIGN KEY (TaskID) REFERENCES Tasks(TaskID) ON DELETE CASCADE,
        CONSTRAINT FK_TimeLogs_User FOREIGN KEY (UserID) REFERENCES Users(UserID),
        CONSTRAINT FK_TimeLogs_ApprovedBy FOREIGN KEY (ApprovedBy) REFERENCES Users(UserID)
    );
    
    PRINT 'TimeLogs table created successfully';
END
GO

-- Attachments table for file management
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Attachments' AND xtype='U')
BEGIN
    CREATE TABLE Attachments (
        AttachmentID INT IDENTITY(1,1) PRIMARY KEY,
        ProjectID INT,
        TaskID INT,
        CommentID INT,
        FileName NVARCHAR(255) NOT NULL,
        OriginalFileName NVARCHAR(255) NOT NULL,
        FilePath NVARCHAR(500) NOT NULL,
        FileSize BIGINT NOT NULL,
        FileType NVARCHAR(50),
        MimeType NVARCHAR(100),
        FileHash NVARCHAR(256), -- SHA-256 hash for integrity
        UploadedBy INT NOT NULL,
        UploadedDate DATETIME2 DEFAULT GETDATE(),
        IsDeleted BIT DEFAULT 0,
        DeletedBy INT,
        DeletedDate DATETIME2,
        DownloadCount INT DEFAULT 0,
        LastAccessDate DATETIME2,
        CONSTRAINT FK_Attachments_Project FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
        CONSTRAINT FK_Attachments_Task FOREIGN KEY (TaskID) REFERENCES Tasks(TaskID) ON DELETE CASCADE,
        CONSTRAINT FK_Attachments_Comment FOREIGN KEY (CommentID) REFERENCES Comments(CommentID) ON DELETE CASCADE,
        CONSTRAINT FK_Attachments_UploadedBy FOREIGN KEY (UploadedBy) REFERENCES Users(UserID),
        CONSTRAINT FK_Attachments_DeletedBy FOREIGN KEY (DeletedBy) REFERENCES Users(UserID)
    );
    
    PRINT 'Attachments table created successfully';
END
GO

-- Activity Logs table for audit trail
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ActivityLogs' AND xtype='U')
BEGIN
    CREATE TABLE ActivityLogs (
        ActivityLogID INT IDENTITY(1,1) PRIMARY KEY,
        UserID INT NOT NULL,
        ProjectID INT,
        TaskID INT,
        Action NVARCHAR(100) NOT NULL,
        Details NVARCHAR(MAX),
        IPAddress NVARCHAR(45),
        UserAgent NVARCHAR(500),
        SessionID NVARCHAR(255),
        CreatedDate DATETIME2 DEFAULT GETDATE(),
        EntityType NVARCHAR(50),
        EntityID INT,
        OldValues NVARCHAR(MAX), -- JSON format
        NewValues NVARCHAR(MAX), -- JSON format
        CONSTRAINT FK_ActivityLogs_User FOREIGN KEY (UserID) REFERENCES Users(UserID),
        CONSTRAINT FK_ActivityLogs_Project FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID),
        CONSTRAINT FK_ActivityLogs_Task FOREIGN KEY (TaskID) REFERENCES Tasks(TaskID)
    );
    
    PRINT 'ActivityLogs table created successfully';
END
GO

-- ============================================================================
-- PERFORMANCE INDEXES
-- ============================================================================

-- Users indexes
CREATE INDEX IX_Users_Username ON Users(Username);
CREATE INDEX IX_Users_Email ON Users(Email);
CREATE INDEX IX_Users_Role ON Users(Role);
CREATE INDEX IX_Users_Active ON Users(Active);
CREATE INDEX IX_Users_LastLoginDate ON Users(LastLoginDate);

-- Projects indexes
CREATE INDEX IX_Projects_Status ON Projects(Status);
CREATE INDEX IX_Projects_Priority ON Projects(Priority);
CREATE INDEX IX_Projects_CreatedBy ON Projects(CreatedBy);
CREATE INDEX IX_Projects_StartDate ON Projects(StartDate);
CREATE INDEX IX_Projects_EndDate ON Projects(EndDate);
CREATE INDEX IX_Projects_Category ON Projects(Category);

-- Tasks indexes
CREATE INDEX IX_Tasks_ProjectID ON Tasks(ProjectID);
CREATE INDEX IX_Tasks_AssigneeID ON Tasks(AssigneeID);
CREATE INDEX IX_Tasks_Status ON Tasks(Status);
CREATE INDEX IX_Tasks_Priority ON Tasks(Priority);
CREATE INDEX IX_Tasks_DueDate ON Tasks(DueDate);
CREATE INDEX IX_Tasks_ParentTaskID ON Tasks(ParentTaskID);

-- Time Logs indexes
CREATE INDEX IX_TimeLogs_TaskID ON TimeLogs(TaskID);
CREATE INDEX IX_TimeLogs_UserID ON TimeLogs(UserID);
CREATE INDEX IX_TimeLogs_LogDate ON TimeLogs(LogDate);
CREATE INDEX IX_TimeLogs_StartTime ON TimeLogs(StartTime);

-- Activity Logs indexes
CREATE INDEX IX_ActivityLogs_UserID ON ActivityLogs(UserID);
CREATE INDEX IX_ActivityLogs_ProjectID ON ActivityLogs(ProjectID);
CREATE INDEX IX_ActivityLogs_TaskID ON ActivityLogs(TaskID);
CREATE INDEX IX_ActivityLogs_CreatedDate ON ActivityLogs(CreatedDate);
CREATE INDEX IX_ActivityLogs_Action ON ActivityLogs(Action);

PRINT 'Performance indexes created successfully';
GO

-- ============================================================================
-- DEFAULT DATA
-- ============================================================================

-- Insert default admin user
IF NOT EXISTS (SELECT 1 FROM Users WHERE Username = 'admin')
BEGIN
    INSERT INTO Users (Username, PasswordHash, Email, FirstName, LastName, Role, Active)
    VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeA8pTQN6C0Sz6.SK', 
            'admin@projectmanagerpro.com', 'System', 'Administrator', 'Admin', 1);
    
    PRINT 'Default admin user created: admin/admin123';
END
GO

-- Insert sample project categories
IF NOT EXISTS (SELECT 1 FROM Projects WHERE ProjectName = 'Sample Project')
BEGIN
    DECLARE @AdminID INT = (SELECT UserID FROM Users WHERE Username = 'admin');
    
    INSERT INTO Projects (ProjectName, Description, Status, Priority, CreatedBy, LastModifiedBy)
    VALUES ('Sample Project', 'This is a sample project to demonstrate the system capabilities', 
            'Active', 'High', @AdminID, @AdminID);
    
    PRINT 'Sample project created';
END
GO

PRINT '🚀 Project Manager Pro v3.0 database setup completed successfully!';
PRINT '';
PRINT 'Default Credentials:';
PRINT 'Username: admin';
PRINT 'Password: admin123';
PRINT '';
PRINT 'Next Steps:';
PRINT '1. Update connection string in .streamlit/secrets.toml';
PRINT '2. Install required Python packages: pip install -r requirements.txt';
PRINT '3. Run the application: streamlit run app.py';
GO