# 🚗 DENSO Project Manager Pro

ระบบจัดการโครงการสำหรับ DENSO ที่พัฒนาด้วย Streamlit และ SQL Server

## 📋 สารบัญ

- [คุณสมบัติหลัก](#-คุณสมบัติหลัก)
- [ความต้องการของระบบ](#️-ความต้องการของระบบ)
- [การติดตั้ง](#-การติดตั้ง)
- [การตั้งค่า](#️-การตั้งค่า)
- [การใช้งาน](#-การใช้งาน)
- [โครงสร้างโปรเจค](#-โครงสร้างโปรเจค)
- [การบำรุงรักษา](#-การบำรุงรักษา)
- [การแก้ไขปัญหา](#-การแก้ไขปัญหา)

## ✨ คุณสมบัติหลัก

### 🔐 การจัดการผู้ใช้และสิทธิ์

- ระบบ Authentication และ Authorization
- การจัดการบทบาทผู้ใช้ (Admin, Project Manager, Team Lead, Developer, User, Viewer)
- การรีเซ็ตรหัสผ่านและการบังคับเปลี่ยนรหัสผ่าน
- การป้องกัน Brute Force Attack

### 📁 การจัดการโครงการ

- สร้าง แก้ไข และลบโครงการ
- ติดตามสถานะและความคืบหน้าโครงการ
- การจัดการงบประมาณและไทม์ไลน์
- การมอบหมายสมาชิกทีม

### ✅ การจัดการงาน

- สร้างและมอบหมายงาน
- การติดตามสถานะงาน (To Do, In Progress, Review, Testing, Done)
- การกำหนดระดับความสำคัญ (Low, Medium, High, Critical)
- การตั้งค่า Dependencies ระหว่างงาน
- การแจ้งเตือนงานที่เลยกำหนด

### 📊 รายงานและการวิเคราะห์

- Dashboard ภาพรวมระบบ
- รายงานความคืบหน้าโครงการ
- วิเคราะห์ประสิทธิภาพทีม
- กราฟและแผนภูมิแบบเรียลไทม์
- การส่งออกรายงานในรูปแบบ CSV

### ⚙️ การตั้งค่าระบบ

- การตั้งค่าทั่วไป (ธีม, ภาษา, การแสดงผล)
- การตั้งค่าความปลอดภัย (รหัสผ่าน, การล็อกอิน)
- การตั้งค่าการแจ้งเตือนและอีเมล
- การสำรองและกู้คืนข้อมูล

### 🗄️ การจัดการฐานข้อมูล (Admin เท่านั้น)

- ดูภาพรวมฐานข้อมูล
- การรัน SQL Query แบบ Read-only
- การสำรองและกู้คืนข้อมูล
- การตรวจสอบประสิทธิภาพและความสมบูรณ์

## 🖥️ ความต้องการของระบบ

### ระบบปฏิบัติการ

- Windows 10/11 หรือ Windows Server 2016+
- Linux (Ubuntu 18.04+, CentOS 7+)
- macOS 10.14+

### ซอฟต์แวร์ที่จำเป็น

- **Python 3.8+** (แนะนำ 3.11)
- **SQL Server 2017+** หรือ **SQL Server Express**
- **ODBC Driver 17 for SQL Server**
- **Git** (สำหรับการ Clone โปรเจค)

### Hardware ขั้นต่ำ

- **RAM:** 4 GB (แนะนำ 8 GB+)
- **CPU:** 2 Cores (แนะนำ 4 Cores+)
- **Storage:** 10 GB ว่าง (แนะนำ 20 GB+)
- **Network:** Internet connection สำหรับการอัปเดต

## 🚀 การติดตั้ง

### 1. Clone โปรเจค

```bash
git clone https://github.com/your-org/denso-project-manager.git
cd denso-project-manager
```

### 2. สร้าง Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. ติดตั้ง Dependencies

```bash
pip install -r requirements.txt
```

### 4. สร้างโครงสร้างโฟลเดอร์

```bash
python setup_directories.py
```

### 5. ตั้งค่าฐานข้อมูล

```bash
# รัน SQL Script ใน SQL Server Management Studio
# หรือใช้ sqlcmd
sqlcmd -S your_server -d master -i setup.sql
```

## ⚙️ การตั้งค่า

### 1. คัดลอกไฟล์ Config

```bash
# คัดลอกไฟล์ตัวอย่าง
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
cp config/app_config.yaml.example config/app_config.yaml
```

### 2. แก้ไขการตั้งค่าฐานข้อมูล

แก้ไขไฟล์ `.streamlit/secrets.toml`:

```toml
[database]
server = "your_sql_server"
database = "ProjectManagerDB"
username = "your_username"
password = "your_password"
driver = "ODBC Driver 17 for SQL Server"
```

### 3. ตั้งค่าความปลอดภัย

สร้าง Secret Keys ใหม่:

```python
import secrets

# สร้าง secret key สำหรับแอป
app_secret = secrets.token_urlsafe(32)
print(f"app.secret_key = \"{app_secret}\"")

# สร้าง keys สำหรับการเข้ารหัส
encryption_key = secrets.token_urlsafe(32)
print(f"security.data_encryption_key = \"{encryption_key}\"")
```

### 4. ตั้งค่าอีเมล (ถ้าต้องการ)

```toml
[email]
smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_username = "your_email@gmail.com"
smtp_password = "your_app_password"
from_email = "noreply@denso.com"
enable_ssl = true
```

## 🏃 การใช้งาน

### 1. เริ่มต้นแอปพลิเคชัน

```bash
streamlit run app.py
```

### 2. เข้าสู่ระบบ

- เปิดเบราว์เซอร์ไปที่: `http://localhost:8501`
- ใช้บัญชี Admin เริ่มต้น:
  - **Username:** `admin`
  - **Password:** `admin123`

### 3. การตั้งค่าเริ่มต้น

1. **เปลี่ยนรหัสผ่าน Admin:** ไปที่ Settings > โปรไฟล์
2. **สร้างผู้ใช้:** ไปที่ การจัดการผู้ใช้ > เพิ่มผู้ใช้ใหม่
3. **ตั้งค่าระบบ:** ไปที่ Settings > ทั่วไป
4. **ทดสอบอีเมล:** ไปที่ Settings > การแจ้งเตือน

### 4. การใช้งานพื้นฐาน

#### สร้างโครงการใหม่

1. ไปที่หน้า **การจัดการโครงการ**
2. คลิก **➕ สร้างโครงการใหม่**
3. กรอกข้อมูลโครงการ
4. เลือกสมาชิกทีม
5. บันทึก

#### สร้างงานใหม่

1. ไปที่หน้า **การจัดการงาน**
2. คลิก **➕ สร้างงานใหม่**
3. เลือกโครงการ
4. กรอกรายละเอียดงาน
5. มอบหมายผู้รับผิดชอบ
6. บันทึก

#### ดูรายงาน

1. ไปที่หน้า **รายงานและการวิเคราะห์**
2. เลือกช่วงเวลา
3. เลือกประเภทรายงาน
4. ดูข้อมูลและกราฟ
5. ส่งออกรายงาน (ถ้าต้องการ)

## 📁 โครงสร้างโปรเจค

```
DENSO_Project_Manager/
├── app.py                          # ไฟล์หลักสำหรับรันแอป
├── setup_directories.py            # สคริปต์สร้างโฟลเดอร์
├── setup.sql                       # SQL สำหรับสร้างฐานข้อมูล
├── requirements.txt                 # Dependencies
├── .gitignore                      # Git ignore rules
├── README.md                       # คู่มือการใช้งาน
│
├── config/                         # การตั้งค่า
│   ├── __init__.py
│   ├── database.py                 # การจัดการฐานข้อมูล
│   └── app_config.yaml.example     # ตัวอย่างการตั้งค่า
│
├── modules/                        # โมดูลหลัก
│   ├── __init__.py
│   ├── auth.py                     # การจัดการ Authentication
│   ├── ui_components.py            # UI Components
│   ├── projects.py                 # การจัดการโครงการ
│   ├── tasks.py                    # การจัดการงาน
│   ├── users.py                    # การจัดการผู้ใช้
│   ├── analytics.py                # รายงานและวิเคราะห์
│   └── settings.py                 # การตั้งค่าระบบ
│
├── pages/                          # หน้าต่างๆ ของแอป
│   ├── __init__.py
│   ├── dashboard.py                # หน้าแดชบอร์ด
│   ├── projects.py                 # หน้าจัดการโครงการ
│   ├── tasks.py                    # หน้าจัดการงาน
│   ├── analytics.py                # หน้ารายงาน
│   ├── users.py                    # หน้าจัดการผู้ใช้
│   ├── settings.py                 # หน้าตั้งค่า
│   └── database_admin.py           # หน้าจัดการฐานข้อมูล
│
├── utils/                          # Utilities
│   ├── __init__.py
│   ├── error_handler.py            # จัดการข้อผิดพลาด
│   └── performance_monitor.py      # ตรวจสอบประสิทธิภาพ
│
├── .streamlit/                     # Streamlit config
│   ├── secrets.toml                # ข้อมูลลับ (ห้ามนำขึ้น Git)
│   └── secrets.toml.example        # ตัวอย่างการตั้งค่า secrets
│
├── logs/                           # Log files
│   ├── app.log                     # Log ทั่วไป
│   └── errors/                     # Error logs
│
├── data/                           # ข้อมูล
│   ├── uploads/                    # ไฟล์อัปโหลด
│   ├── exports/                    # ไฟล์ส่งออก
│   └── backups/                    # สำรองข้อมูล
│
├── static/                         # Static files
│   ├── css/                        # CSS files
│   ├── js/                         # JavaScript files
│   └── images/                     # รูปภาพ
│
├── reports/                        # รายงานที่สร้าง
├── temp/                           # ไฟล์ชั่วคราว
├── docs/                           # เอกสาร
└── tests/                          # การทดสอบ
```

## 🔧 การบำรุงรักษา

### การสำรองข้อมูลประจำ

1. **การสำรองอัตโนมัติ:**

   - ไปที่ Settings > สำรองข้อมูล
   - เปิดใช้งานการสำรองอัตโนมัติ
   - ตั้งเวลาสำรอง (แนะนำ 02:00 น.)

2. **การสำรองด้วยตนเอง:**

   ```bash
   # ผ่าน Admin Panel
   Database Admin > การดำเนินการ > สำรองข้อมูล

   # หรือผ่าน Command Line
   sqlcmd -S server -E -Q "BACKUP DATABASE [ProjectManagerDB] TO DISK = 'C:\Backups\ProjectManagerDB.bak'"
   ```

### การอัปเดตระบบ

```bash
# 1. สำรองข้อมูลก่อน
# 2. Pull การอัปเดตล่าสุด
git pull origin main

# 3. อัปเดต dependencies
pip install -r requirements.txt --upgrade

# 4. รัน migration (ถ้ามี)
python migrate.py

# 5. รีสตาร์ทแอป
```

### การทำความสะอาดระบบ

```bash
# ทำความสะอาด Log เก่า
python -c "
from modules.settings import SettingsManager
from config.database import DatabaseManager
db = DatabaseManager()
settings = SettingsManager(db)
settings.cleanup_database()
"

# ลบไฟล์ temporary
rm -rf temp/*
rm -rf logs/*.log.old
```

### การตรวจสอบสุขภาพระบบ

1. **ตรวจสอบประสิทธิภาพ:**

   - Database Admin > การตรวจสอบ > วิเคราะห์ฐานข้อมูล

2. **ตรวจสอบความสมบูรณ์:**

   - Database Admin > การตรวจสอบ > ตรวจสอบความสมบูรณ์

3. **ตรวจสอบ Log:**

   ```bash
   tail -f logs/app.log
   ```

## 🔍 การแก้ไขปัญหา

### ปัญหาการเชื่อมต่อฐานข้อมูล

**อาการ:** ไม่สามารถเชื่อมต่อฐานข้อมูลได้

**การแก้ไข:**

1. ตรวจสอบ Connection String ใน `secrets.toml`
2. ตรวจสอบว่า SQL Server เปิดอยู่
3. ตรวจสอบ Firewall และ Port 1433
4. ลองเชื่อมต่อด้วย SQL Server Management Studio

```bash
# ทดสอบการเชื่อมต่อ
python -c "
from config.database import DatabaseManager
db = DatabaseManager()
print('Connection:', db.test_connection())
"
```

### ปัญหาการ Login

**อาการ:** ไม่สามารถล็อกอินได้

**การแก้ไข:**

1. ใช้บัญชี Admin เริ่มต้น: `admin` / `admin123`
2. ตรวจสอบว่าบัญชีไม่ถูกล็อค
3. รีเซ็ตรหัสผ่านผ่าน Database:

```sql
-- รีเซ็ตรหัสผ่าน Admin
UPDATE Users
SET PasswordHash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewLZ.9s5w8nTUOcG',
    FailedLoginAttempts = 0,
    LastFailedLogin = NULL,
    IsLocked = 0
WHERE Username = 'admin';
```

### ปัญหาประสิทธิภาพ

**อาการ:** แอปทำงานช้า

**การแก้ไข:**

1. ตรวจสอบการใช้ RAM และ CPU
2. ทำความสะอาดฐานข้อมูล
3. สร้างดัชนีใหม่:

```sql
-- สร้างดัชนีสำหรับปรับปรุงประสิทธิภาพ
CREATE INDEX IX_Tasks_Status ON Tasks(Status);
CREATE INDEX IX_Tasks_DueDate ON Tasks(DueDate);
CREATE INDEX IX_Projects_Status ON Projects(Status);
```

### ปัญหาการส่งอีเมล

**อาการ:** ไม่สามารถส่งอีเมลแจ้งเตือนได้

**การแก้ไข:**

1. ตรวจสอบการตั้งค่าอีเมลใน `secrets.toml`
2. ใช้ App Password สำหรับ Gmail
3. ทดสอบการส่งอีเมล:
   - Settings > การแจ้งเตือน > ส่งอีเมลทดสอบ

### ปัญหา Port ซ้ำ

**อาการ:** `Error: Port 8501 is already in use`

**การแก้ไข:**

```bash
# หา Process ที่ใช้ Port
netstat -ano | findstr :8501

# Kill Process (Windows)
taskkill /PID <PID> /F

# หรือเปลี่ยน Port
streamlit run app.py --server.port 8502
```

### Log Files สำหรับการ Debug

```bash
# Application Log
tail -f logs/app.log

# Error Log
ls logs/errors/

# Streamlit Log
~/.streamlit/logs/
```

### การติดต่อสำหรับความช่วยเหลือ

- **Email:** <support@denso.com>
- **Internal IT:** ext. 1234
- **GitHub Issues:** [Project Repository Issues](https://github.com/your-org/denso-project-manager/issues)

## 📝 หมายเหตุเพิ่มเติม

### ข้อมูลสำคัญ

- ⚠️ **อย่าลืม:** เปลี่ยนรหัสผ่าน Admin เริ่มต้นทันทีหลังติดตั้ง
- 🔐 **Security:** ไฟล์ `secrets.toml` ต้องไม่นำขึ้น Git
- 💾 **Backup:** ตั้งค่าการสำรองข้อมูลอัตโนมัติ
- 📊 **Performance:** ตรวจสอบประสิทธิภาพระบบเป็นประจำ

### การพัฒนาต่อ

- เพิ่มฟีเจอร์ Mobile App
- Integration กับ Microsoft Teams/Slack
- Advanced Analytics และ AI
- Multi-language Support

---

**DENSO Project Manager Pro**  
พัฒนาโดย: Thammaphon Chattasuwanna (SDM)
อัปเดตล่าสุด: 2025
