# 🚀 DENSO Project Manager Pro - Complete Setup Guide

## 📋 Table of Contents

1. [System Requirements](#system-requirements)
2. [Prerequisites Installation](#prerequisites-installation)
3. [Database Setup](#database-setup)
4. [Application Installation](#application-installation)
5. [Configuration](#configuration)
6. [Security Setup](#security-setup)
7. [Performance Optimization](#performance-optimization)
8. [Deployment](#deployment)
9. [Troubleshooting](#troubleshooting)
10. [Maintenance](#maintenance)

---

## 🖥️ System Requirements

### Minimum Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, Ubuntu 18.04+
- **RAM**: 4GB (8GB recommended)
- **Storage**: 2GB free space (5GB recommended)
- **CPU**: 2 cores minimum (4 cores recommended)
- **Network**: Internet connection for initial setup

### Recommended Requirements

- **RAM**: 16GB or higher
- **Storage**: SSD with 10GB+ free space
- **CPU**: 8 cores or higher
- **Network**: High-speed internet connection

---

## 📦 Prerequisites Installation

### 1. Python Installation

```bash
# Windows (using Chocolatey)
choco install python

# macOS (using Homebrew)
brew install python@3.11

# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-pip python3.11-venv
```

### 2. SQL Server Installation

#### Windows - SQL Server Express

1. Download SQL Server 2019 Express from Microsoft
2. Run the installer with default settings
3. Enable SQL Server Browser service
4. Configure Windows Authentication + Mixed Mode

#### Windows - SQL Server Developer Edition

```powershell
# Using Chocolatey
choco install sql-server-2019

# Or download from Microsoft website
# Choose Developer Edition for full features
```

#### Linux - SQL Server on Docker

```bash
# Pull SQL Server 2019 image
docker pull mcr.microsoft.com/mssql/server:2019-latest

# Run SQL Server container
docker run -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=YourStrong@Password123" \
   -p 1433:1433 --name denso-sql-server \
   -d mcr.microsoft.com/mssql/server:2019-latest
```

#### macOS - SQL Server on Docker

```bash
# Same as Linux instructions above
# Ensure Docker Desktop is installed and running
```

### 3. SQL Server Management Studio (SSMS)

```bash
# Windows only - Download from Microsoft
# For macOS/Linux, use Azure Data Studio instead
```

### 4. Git Installation

```bash
# Windows
choco install git

# macOS
brew install git

# Ubuntu/Debian
sudo apt install git
```

---

## 🗄️ Database Setup

### 1. Create Database

```sql
-- Connect to SQL Server using SSMS or sqlcmd
-- Create database
CREATE DATABASE ProjectManagerDB;
GO

-- Switch to the new database
USE ProjectManagerDB;
GO
```

### 2. Create Database User

```sql
-- Create login (server level)
CREATE LOGIN denso_user WITH PASSWORD = 'SecurePassword123!';
GO

-- Create user (database level)
USE ProjectManagerDB;
CREATE USER denso_user FOR LOGIN denso_user;
GO

-- Grant permissions
ALTER ROLE db_datareader ADD MEMBER denso_user;
ALTER ROLE db_datawriter ADD MEMBER denso_user;
ALTER ROLE db_ddladmin ADD MEMBER denso_user;
GO
```

### 3. Run Database Schema

```bash
# Navigate to project directory and run setup script
cd denso-project-manager
sqlcmd -S localhost -d ProjectManagerDB -i setup.sql

# Or using Windows Authentication
sqlcmd -S localhost -E -d ProjectManagerDB -i setup.sql
```

### 4. Verify Database Setup

```sql
-- Check if tables were created
SELECT TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE';

-- Check if default admin user exists
SELECT * FROM Users WHERE Username = 'admin';
```

---

## 🛠️ Application Installation

### 1. Clone Repository

```bash
# Clone the project
git clone https://github.com/your-org/denso-project-manager.git
cd denso-project-manager

# Or download ZIP and extract
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# Verify installation
pip list
```

### 4. Install Additional Dependencies (Optional)

```bash
# For enhanced performance (Redis caching)
pip install redis

# For email notifications
pip install sendgrid

# For advanced analytics
pip install scikit-learn pandas numpy
```

---

## ⚙️ Configuration

### 1. Create Configuration Directory

```bash
mkdir -p .streamlit
mkdir -p logs
mkdir -p config
```

### 2. Create Streamlit Secrets File

```toml
# .streamlit/secrets.toml
[database]
server = "localhost"
database = "ProjectManagerDB"
username = "denso_user"
password = "SecurePassword123!"
driver = "ODBC Driver 17 for SQL Server"

[database.connection_options]
encrypt = "yes"
trust_server_certificate = "yes"
connection_timeout = 30
command_timeout = 60

[app]
debug = false
log_level = "INFO"
secret_key = "your-super-secret-key-change-this"
session_timeout = 3600
max_upload_size = 50

[security]
bcrypt_rounds = 12
session_cookie_secure = false
password_min_length = 8
max_login_attempts = 5
lockout_duration = 900

[features]
enable_notifications = true
enable_file_upload = true
enable_analytics = true
enable_performance_monitoring = true
```

### 3. Create Application Configuration

```yaml
# config/app_config.yaml
app:
  app_name: 'DENSO Project Manager Pro'
  version: '2.0.0'
  debug: false
  log_level: 'INFO'
  environment: 'production'
  max_upload_size_mb: 50
  timezone: 'UTC'
  language: 'en'

cache:
  max_size_mb: 100
  default_ttl: 3600
  redis_enabled: false
  redis_host: 'localhost'
  redis_port: 6379

performance:
  enable_monitoring: true
  page_load_threshold: 2.0
  memory_threshold_mb: 512
  db_query_threshold: 1.0
  cache_hit_rate_threshold: 80.0

notifications:
  enable_notifications: true
  check_interval: 300
  max_notifications_per_user: 50
  default_priority: 'medium'

ui:
  theme: 'light'
  enable_animations: true
  enable_glassmorphism: true
  default_page_size: 20
  compact_mode: false
```

### 4. Environment Variables (Optional)

```bash
# Create .env file for environment variables
echo "DB_SERVER=localhost" > .env
echo "DB_DATABASE=ProjectManagerDB" >> .env
echo "DB_USERNAME=denso_user" >> .env
echo "DB_PASSWORD=SecurePassword123!" >> .env
echo "SECRET_KEY=your-super-secret-key" >> .env
echo "ENVIRONMENT=production" >> .env
```

---

## 🔒 Security Setup

### 1. Generate Secret Keys

```python
# Run this to generate secure secret keys
import secrets

print("Secret Key:", secrets.token_urlsafe(32))
print("CSRF Secret:", secrets.token_urlsafe(24))
print("JWT Secret:", secrets.token_urlsafe(32))
```

### 2. Configure HTTPS (Production)

```bash
# Generate SSL certificate (for production)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Update streamlit config for HTTPS
echo "server.enableCORS = false" >> .streamlit/config.toml
echo "server.enableXsrfProtection = true" >> .streamlit/config.toml
```

### 3. Database Security

```sql
-- Enable encryption (if supported)
ALTER DATABASE ProjectManagerDB
SET ENCRYPTION ON;

-- Create backup encryption key
CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'YourStrongPassword123!';

-- Regular maintenance
BACKUP DATABASE ProjectManagerDB
TO DISK = 'C:\Backup\ProjectManagerDB.bak'
WITH COMPRESSION, ENCRYPTION (
    ALGORITHM = AES_256,
    SERVER CERTIFICATE = YourServerCertificate
);
```

### 4. Firewall Configuration

```bash
# Windows Firewall
netsh advfirewall firewall add rule name="DENSO PM" dir=in action=allow protocol=TCP localport=8501

# Ubuntu UFW
sudo ufw allow 8501/tcp
sudo ufw enable

# Check if ports are open
netstat -an | grep 8501
```

---

## ⚡ Performance Optimization

### 1. Database Optimization

```sql
-- Create indexes for better performance
USE ProjectManagerDB;

-- Project indexes
CREATE INDEX IX_Projects_Status_Priority ON Projects(Status, Priority);
CREATE INDEX IX_Projects_CreatedDate ON Projects(CreatedDate);
CREATE INDEX IX_Projects_EndDate ON Projects(EndDate);

--
```
