-- database/setup.sql
-- Project Manager Pro v3.0 Database Setup Script

-- Create Database
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'ProjectManagerDB')
BEGIN
    CREATE DATABASE ProjectManagerDB;
END
GO

USE ProjectManagerDB;
GO

-- Users Table
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
        Active BIT DEFAULT 1,
        CreatedDate DATETIME DEFAULT GETDATE(),
        LastLoginDate DATETIME,
        PasswordChangedDate DATETIME,
        ProfilePicture NVARCHAR(500),
        Department NVARCHAR(100),
        PhoneNumber NVARCHAR(20),
        Bio NTEXT,
        Timezone NVARCHAR(50) DEFAULT 'UTC',
        Language NVARCHAR(10) DEFAULT 'en',
        Theme NVARCHAR(50) DEFAULT 'auto',
        NotificationSettings NTEXT -- JSON string
    );
END
GO

-- Projects Table
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Projects' AND xtype='U')
BEGIN
    CREATE TABLE Projects (
        ProjectID INT IDENTITY(1,1) PRIMARY KEY,
        ProjectName NVARCHAR(200) NOT NULL,
        Description NTEXT,
        StartDate DATE,
        EndDate DATE,
        Status NVARCHAR(50) DEFAULT 'Planning' CHECK (Status IN ('Planning', 'In Progress', 'On Hold', 'Completed', 'Cancelled')),
        Priority NVARCHAR(50) DEFAULT 'Medium' CHECK (Priority IN ('Low', 'Medium', 'High', 'Critical')),
        Budget DECIMAL(18,2),
        ClientName NVARCHAR(200),
        CreatedBy INT,
        CreatedDate DATETIME DEFAULT GETDATE(),
        LastModifiedDate DATETIME DEFAULT GETDATE(),
        Tags NVARCHAR(500),
        Progress INT DEFAULT 0 CHECK (Progress >= 0 AND Progress <= 100),
        ActualBudget DECIMAL(18,2),
        EstimatedHours DECIMAL(8,2),
        ActualHours DECIMAL(8,2),
        FOREIGN KEY (CreatedBy) REFERENCES Users(UserID)
    );
END
GO

-- Tasks Table
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
        CreatedBy INT,
        CreatedDate DATETIME DEFAULT GETDATE(),
        LastModifiedDate DATETIME DEFAULT GETDATE(),
        CompletedDate DATETIME,
        Comments NTEXT,
        Attachments NTEXT, -- JSON string of file paths
        FOREIGN KEY (ProjectID) REFERENCES Projects(ProjectID) ON DELETE CASCADE,
        FOREIGN KEY (AssigneeID) REFERENCES Users(UserID),
        FOREIGN KEY (CreatedBy) REFERENCES Users(UserID)
    );
END
GO

-- Project Members Table (Many-to-Many relationship)
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
END
GO

-- Time Tracking Table
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
END
GO

-- Comments Table
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
        FOREIGN KEY (UserID) REFERENCES Users(UserID),
        FOREIGN KEY (ParentCommentID) REFERENCES Comments(CommentID)
    );
END
GO

-- Notifications Table
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
        FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
    );
END
GO

-- Create Indexes for Performance
CREATE NONCLUSTERED INDEX IX_Tasks_ProjectID ON Tasks(ProjectID);
CREATE NONCLUSTERED INDEX IX_Tasks_AssigneeID ON Tasks(AssigneeID);
CREATE NONCLUSTERED INDEX IX_Tasks_Status ON Tasks(Status);
CREATE NONCLUSTERED INDEX IX_Tasks_DueDate ON Tasks(DueDate);
CREATE NONCLUSTERED INDEX IX_Projects_Status ON Projects(Status);
CREATE NONCLUSTERED INDEX IX_Projects_CreatedBy ON Projects(CreatedBy);
CREATE NONCLUSTERED INDEX IX_Users_Username ON Users(Username);
CREATE NONCLUSTERED INDEX IX_Users_Email ON Users(Email);
CREATE NONCLUSTERED INDEX IX_Comments_EntityType_EntityID ON Comments(EntityType, EntityID);
CREATE NONCLUSTERED INDEX IX_Notifications_UserID_IsRead ON Notifications(UserID, IsRead);
GO

-- Insert Default Admin User (password is 'admin123' hashed with bcrypt)
IF NOT EXISTS (SELECT * FROM Users WHERE Username = 'admin')
BEGIN
    INSERT INTO Users (Username, PasswordHash, Email, FirstName, LastName, Role, Department)
    VALUES (
        'admin',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewLZ.9s5w8nTUOcG',
        'admin@projectmanager.local',
        'System',
        'Administrator',
        'Admin',
        'IT'
    );
END
GO

-- Insert Sample Data (Optional)
IF NOT EXISTS (SELECT * FROM Projects WHERE ProjectName = 'Website Redesign')
BEGIN
    INSERT INTO Projects (ProjectName, Description, StartDate, EndDate, Status, Priority, Budget, ClientName, CreatedBy)
    VALUES (
        'Website Redesign',
        'Complete redesign of company website with modern UI/UX',
        '2024-01-01',
        '2024-03-31',
        'In Progress',
        'High',
        50000.00,
        'Internal Project',
        1
    );
END
GO

PRINT 'Database setup completed successfully!';