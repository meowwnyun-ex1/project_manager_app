

DECLARE @DatabaseName NVARCHAR(128) = N'ProjectManagerDB'
DECLARE @SQL NVARCHAR(MAX)

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = @DatabaseName)
BEGIN
    PRINT 'Hello' + @DatabaseName
    SET @SQL = 'CREATE DATABASE [' + @DatabaseName + ']'
    EXEC sp_executesql @SQL
END
ELSE
BEGIN
    PRINT 'Hello' + @DatabaseName + 'Hello'
END
GO 
USE ProjectManagerDB
GO

PRINT 'Hello' + DB_NAME()

IF NOT EXISTS (SELECT 1 FROM sys.database_query_store_options WHERE actual_state = 1)
BEGIN
    PRINT 'Hello' + DB_NAME() + '...'
    ALTER DATABASE CURRENT
    SET QUERY_STORE = ON
    (
        OPERATION_MODE = READ_WRITE,
        CLEANUP_POLICY = ( STALE_QUERY_THRESHOLD_DAYS = 30 ),
        DATA_FLUSH_INTERVAL_SECONDS = 900,
        MAX_STORAGE_SIZE_MB = 1024,
        INTERVAL_LENGTH_MINUTES = 60,
        SIZE_BASED_CLEANUP_MODE = AUTO,
        MAX_PLANS_PER_QUERY = 200
    )
    PRINT 'Hello'
END
ELSE
BEGIN
    PRINT 'Hello' + DB_NAME()
END
GO

USE ProjectManagerDB
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Users' AND type = 'U')
BEGIN
    PRINT 'Hello'
    CREATE TABLE Users (
        UserID INT PRIMARY KEY IDENTITY(1,1),
        Username NVARCHAR(50) NOT NULL UNIQUE,
        PasswordHash NVARCHAR(255) NOT NULL,
        Role NVARCHAR(20) DEFAULT 'User',
        CreatedDate DATETIME DEFAULT GETDATE()
    )
    PRINT 'Hello'
END
ELSE
BEGIN
    PRINT 'Hello'
END
GO


USE ProjectManagerDB
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Projects' AND type = 'U')
BEGIN
    PRINT 'Hello'
    CREATE TABLE Projects (
        ProjectID INT PRIMARY KEY IDENTITY(1,1),
        ProjectName NVARCHAR(100) NOT NULL,
        Description NVARCHAR(MAX),
        StartDate DATE,
        EndDate DATE,
        Status NVARCHAR(50) DEFAULT 'Planning',
        CreatedDate DATETIME DEFAULT GETDATE()
    )
    PRINT 'Hello'
END
ELSE
BEGIN
    PRINT 'Hello'
END
GO

USE ProjectManagerDB
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Tasks' AND type = 'U')
BEGIN
    PRINT 'Hello'
    CREATE TABLE Tasks (
        TaskID INT PRIMARY KEY IDENTITY(1,1),
        ProjectID INT FOREIGN KEY REFERENCES Projects(ProjectID) ON DELETE CASCADE,
        TaskName NVARCHAR(100) NOT NULL,
        Description NVARCHAR(MAX),
        StartDate DATE,
        EndDate DATE,
        AssigneeID INT FOREIGN KEY REFERENCES Users(UserID),
        Status NVARCHAR(50) DEFAULT 'To Do',
        Progress INT DEFAULT 0,
        CreatedDate DATETIME DEFAULT GETDATE()
    )
    PRINT 'Hello'
END
ELSE
BEGIN
    PRINT 'Hello'
END
GO

PRINT 'Hello'