import os
import shutil


def clear_pycache_concise(path="."):
    """
    ค้นหาและลบโฟลเดอร์ __pycache__ ทั้งหมดในเส้นทางที่กำหนด
    โดยแสดงข้อความที่กระชับขึ้น
    """
    deleted_count = 0
    error_count = 0
    for root, dirs, files in os.walk(path):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            try:
                shutil.rmtree(pycache_path)
                deleted_count += 1
            except OSError as e:
                # พิมพ์ข้อผิดพลาดเฉพาะในกรณีที่ลบไม่ได้จริงๆ
                print(f"ไม่สามารถลบ {pycache_path} ได้: {e}")
                error_count += 1

    if deleted_count > 0:
        print(f"ลบโฟลเดอร์ __pycache__ ไปแล้ว {deleted_count} แห่ง.")
    else:
        print("ไม่พบโฟลเดอร์ __pycache__ ในโปรเจกต์นี้.")

    if error_count > 0:
        print(f"มีข้อผิดพลาดในการลบ {error_count} โฟลเดอร์. โปรดตรวจสอบสิทธิ์การเข้าถึง.")


if __name__ == "__main__":
    print("กำลังเริ่มต้นการล้าง __pycache__...")
    clear_pycache_concise()
    print("การล้าง __pycache__ เสร็จสมบูรณ์.")
