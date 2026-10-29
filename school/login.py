import tkinter as tk
from tkinter import messagebox
import sqlite3

DB_PATH = "school_system.db"

# إنشاء جدول المستخدمين لو مش موجود
def init_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)
    # إضافة مستخدم افتراضي (مدير)
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?,?,?)",
              ("admin", "1234", "مدير"))
    conn.commit()
    conn.close()

def check_login(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

def main_menu(role):
    menu = tk.Toplevel()
    menu.title("القائمة الرئيسية - نظام المدرسة")
    menu.geometry("600x400")
    tk.Label(menu, text=f"مرحبا بك، {role}", font=("Arial", 16)).pack(pady=20)
    # أزرار للأقسام
    tk.Button(menu, text="👨‍🎓 الطلاب", width=20).pack(pady=5)
    tk.Button(menu, text="👩‍🏫 المعلمين", width=20).pack(pady=5)
    tk.Button(menu, text="📅 الجدول الدراسي", width=20).pack(pady=5)
    tk.Button(menu, text="💰 الشؤون المالية", width=20).pack(pady=5)
    tk.Button(menu, text="📑 التقارير والطباعة", width=20).pack(pady=5)
    tk.Button(menu, text="💾 النسخ الاحتياطي", width=20).pack(pady=5)

def login_screen():
    root = tk.Tk()
    root.title("تسجيل الدخول - نظام المدرسة")
    root.geometry("400x300")
    root.resizable(False, False)

    tk.Label(root, text="نظام إدارة المدرسة", font=("Arial", 18, "bold")).pack(pady=10)

    frame = tk.Frame(root)
    frame.pack(pady=20)

    tk.Label(frame, text="اسم المستخدم:").grid(row=0, column=0, pady=5, sticky="e")
    username_entry = tk.Entry(frame)
    username_entry.grid(row=0, column=1, pady=5)

    tk.Label(frame, text="كلمة المرور:").grid(row=1, column=0, pady=5, sticky="e")
    password_entry = tk.Entry(frame, show="*")
    password_entry.grid(row=1, column=1, pady=5)

    def on_login():
        u = username_entry.get()
        p = password_entry.get()
        role = check_login(u, p)
        if role:
            messagebox.showinfo("تم الدخول", f"مرحبا {u} - الصلاحية: {role}")
            root.withdraw()  # إخفاء نافذة الدخول
            main_menu(role)
        else:
            messagebox.showerror("خطأ", "اسم المستخدم أو كلمة المرور غير صحيحة")

    tk.Button(root, text="تسجيل الدخول", command=on_login, width=15).pack(pady=10)
    tk.Button(root, text="خروج", command=root.destroy, width=15).pack()

    root.mainloop()

if __name__ == "__main__":
    init_users()
    login_screen()
