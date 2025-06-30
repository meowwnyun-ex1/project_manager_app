import os
import shutil


def clear_pycache(root_dir):
    """
    ค้นหาและลบโฟลเดอร์ __pycache__ ทั้งหมดใน root_dir
    และไดเรกทอรีย่อย
    """
    deleted_count = 0
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if "__pycache__" in dirnames:
            pycache_path = os.path.join(dirpath, "__pycache__")
            try:
                shutil.rmtree(pycache_path)
                print(f"ลบ: {pycache_path}")
                deleted_count += 1
            except OSError as e:
                print(f"ไม่สามารถลบ {pycache_path}: {e}")
    if deleted_count == 0:
        print("ไม่พบโฟลเดอร์ __pycache__ ในโปรเจกต์นี้")
    else:
        print(f"\nลบโฟลเดอร์ __pycache__ ไปแล้ว {deleted_count} โฟลเดอร์")


if __name__ == "__main__":
    # รันจากไดเรกทอรีที่ต้องการเคลียร์ หรือระบุพาธ
    # current_directory = os.getcwd() # หากต้องการเคลียร์เฉพาะในไดเรกทอรีปัจจุบัน
    # clear_pycache(current_directory)

    # หากต้องการเคลียร์ในไดเรกทอรีที่รันสคริปต์นี้และทุกๆ โฟลเดอร์ย่อย
    clear_pycache(os.path.dirname(os.path.abspath(__file__)))
    print("\n--- เสร็จสิ้นการเคลียร์ __pycache__ ---")
