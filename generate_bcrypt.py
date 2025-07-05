#!/usr/bin/env python3
"""
สคริปต์สร้าง bcrypt hash สำหรับรหัสผ่าน DENSO Team
"""
import bcrypt

# รายการรหัสผ่านที่ต้องการ hash
passwords = [
    {"username": "TS00029", "password": "Thammaphon@TS00029"},
    {"username": "03954", "password": "Nattha@03954"},
    {"username": "05600", "password": "Waratcharpon@05600"},
    {"username": "FS00055", "password": "Thanespong@FS00055"},
    {"username": "TN00242", "password": "Chanakarn@TN00242"},
    {"username": "TN00243", "password": "Narissara@TN00243"},
]

print("🔐 กำลังสร้าง bcrypt hash สำหรับรหัสผ่าน DENSO Team...")
print("=" * 60)

for user in passwords:
    # สร้าง salt และ hash
    salt = bcrypt.gensalt(rounds=12)
    password_hash = bcrypt.hashpw(user["password"].encode("utf-8"), salt)
    hash_string = password_hash.decode("utf-8")

    print(f"-- Hash สำหรับ {user['password']}")
    print(f"('{user['username']}', '{hash_string}',")
    print()

print("✅ เสร็จสิ้น! copy hash เหล่านี้ไปใส่ในไฟล์ SQL ได้เลย")

# ทดสอบ verification
print("\n🧪 ทดสอบ verification:")
for user in passwords:
    salt = bcrypt.gensalt(rounds=12)
    password_hash = bcrypt.hashpw(user["password"].encode("utf-8"), salt)

    # ทดสอบว่า hash ตรงกับรหัสผ่านหรือไม่
    is_valid = bcrypt.checkpw(user["password"].encode("utf-8"), password_hash)
    print(f"✓ {user['username']}: {'PASS' if is_valid else 'FAIL'}")
