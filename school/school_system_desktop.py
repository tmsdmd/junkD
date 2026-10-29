# school_system_desktop.py
# نظام إدارة مدرسة بسيط - Desktop App (Tkinter + SQLite)
# يعمل على Python 3.8+
import os, sqlite3, datetime, shutil, csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

APP_DB = os.path.join(os.path.dirname(__file__), "school_system.db")
BACKUP_DIR = os.path.join(os.path.dirname(__file__), "backups")

# -----------------------
# Database utilities
# -----------------------
def get_conn(path=APP_DB):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
    PRAGMA foreign_keys = ON;
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        first_name TEXT,
        last_name TEXT,
        dob TEXT,
        phone TEXT,
        address TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        first_name TEXT,
        last_name TEXT,
        phone TEXT,
        subject TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE,
        title TEXT,
        grade_level TEXT,
        fee REAL DEFAULT 0,
        notes TEXT
    );
    CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        course_id INTEGER,
        enrollment_date TEXT DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'active',
        FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        teacher_id INTEGER,
        weekday TEXT,
        start_time TEXT,
        end_time TEXT,
        room TEXT,
        notes TEXT,
        FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE SET NULL,
        FOREIGN KEY(teacher_id) REFERENCES teachers(id) ON DELETE SET NULL
    );
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        amount REAL,
        method TEXT,
        note TEXT,
        paid_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE SET NULL
    );
    """)
    conn.commit()
    conn.close()

# -----------------------
# CRUD functions
# -----------------------
# Students
def add_student(data):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO students(code, first_name, last_name, dob, phone, address, notes)
                 VALUES(?,?,?,?,?,?,?)""", (data['code'], data['first_name'], data['last_name'],
                                           data.get('dob'), data.get('phone'), data.get('address'),
                                           data.get('notes')))
    conn.commit(); conn.close()

def update_student(student_id, fields):
    conn = get_conn()
    cols = ", ".join([f"{k}=?" for k in fields.keys()])
    vals = list(fields.values()) + [student_id]
    conn.execute(f"UPDATE students SET {cols} WHERE id=?", vals)
    conn.commit(); conn.close()

def delete_student(student_id):
    conn = get_conn()
    conn.execute("DELETE FROM students WHERE id=?", (student_id,))
    conn.commit(); conn.close()

def fetch_students(filter_text=None):
    conn = get_conn()
    q = "SELECT * FROM students"
    params = []
    if filter_text:
        q += " WHERE code LIKE ? OR first_name LIKE ? OR last_name LIKE ?"
        like = f"%{filter_text}%"
        params = [like, like, like]
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return rows

# Teachers
def add_teacher(data):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO teachers(code, first_name, last_name, phone, subject, notes)
                 VALUES(?,?,?,?,?,?)""", (data['code'], data['first_name'], data['last_name'],
                                           data.get('phone'), data.get('subject'), data.get('notes')))
    conn.commit(); conn.close()

def fetch_teachers():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM teachers").fetchall()
    conn.close()
    return rows

def update_teacher(tid, fields):
    conn = get_conn()
    cols = ", ".join([f"{k}=?" for k in fields.keys()])
    vals = list(fields.values()) + [tid]
    conn.execute(f"UPDATE teachers SET {cols} WHERE id=?", vals)
    conn.commit(); conn.close()

def delete_teacher(tid):
    conn = get_conn()
    conn.execute("DELETE FROM teachers WHERE id=?", (tid,))
    conn.commit(); conn.close()

# Courses
def add_course(data):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO courses(code, title, grade_level, fee, notes)
                 VALUES(?,?,?,?,?)""", (data['code'], data['title'], data.get('grade_level'),
                                         data.get('fee',0), data.get('notes')))
    conn.commit(); conn.close()

def fetch_courses():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM courses").fetchall()
    conn.close()
    return rows

def update_course(cid, fields):
    conn = get_conn()
    cols = ", ".join([f"{k}=?" for k in fields.keys()])
    vals = list(fields.values()) + [cid]
    conn.execute(f"UPDATE courses SET {cols} WHERE id=?", vals)
    conn.commit(); conn.close()

def delete_course(cid):
    conn = get_conn()
    conn.execute("DELETE FROM courses WHERE id=?", (cid,))
    conn.commit(); conn.close()

# Enrollments
def enroll_student(student_id, course_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO enrollments(student_id, course_id) VALUES(?,?)", (student_id, course_id))
    conn.commit(); conn.close()

def fetch_enrollments():
    conn = get_conn()
    rows = conn.execute("""SELECT e.id, s.code AS student_code, s.first_name || ' ' || s.last_name AS student,
                          c.code AS course_code, c.title AS course, e.enrollment_date, e.status
                          FROM enrollments e
                          JOIN students s ON s.id=e.student_id
                          JOIN courses c ON c.id=e.course_id
                          """).fetchall()
    conn.close()
    return rows

def delete_enrollment(eid):
    conn = get_conn()
    conn.execute("DELETE FROM enrollments WHERE id=?", (eid,))
    conn.commit(); conn.close()

# Schedules
def add_schedule(data):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""INSERT INTO schedules(course_id, teacher_id, weekday, start_time, end_time, room, notes)
                 VALUES(?,?,?,?,?,?,?)""", (data['course_id'], data['teacher_id'], data['weekday'],
                                           data.get('start_time'), data.get('end_time'), data.get('room'),
                                           data.get('notes')))
    conn.commit(); conn.close()

def fetch_schedules():
    conn = get_conn()
    rows = conn.execute("""SELECT sch.id, c.code AS course_code, c.title AS course, t.code AS teacher_code,
                          t.first_name || ' ' || t.last_name AS teacher, sch.weekday, sch.start_time, sch.end_time, sch.room
                          FROM schedules sch
                          LEFT JOIN courses c ON c.id=sch.course_id
                          LEFT JOIN teachers t ON t.id=sch.teacher_id
                       """).fetchall()
    conn.close()
    return rows

def delete_schedule(sid):
    conn = get_conn()
    conn.execute("DELETE FROM schedules WHERE id=?", (sid,))
    conn.commit(); conn.close()

# Payments
def add_payment(student_id, amount, method, note):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO payments(student_id, amount, method, note) VALUES(?,?,?,?)",
              (student_id, float(amount), method, note))
    conn.commit(); conn.close()

def fetch_payments():
    conn = get_conn()
    rows = conn.execute("""SELECT p.id, p.amount, p.method, p.paid_at, s.code AS student_code,
                          s.first_name || ' ' || s.last_name AS student
                          FROM payments p
                          LEFT JOIN students s ON s.id=p.student_id
                       """).fetchall()
    conn.close()
    return rows

def finance_summary():
    conn = get_conn()
    r = conn.execute("SELECT SUM(amount) AS total, COUNT(*) AS count FROM payments").fetchone()
    conn.close()
    return dict(r) if r else {"total":0,"count":0}

# Backup / restore
def make_backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(BACKUP_DIR, f"school_system_backup_{ts}.db")
    shutil.copy2(APP_DB, dest)
    return dest

def restore_backup(file_path):
    shutil.copy2(file_path, APP_DB)

# -----------------------
# GUI
# -----------------------
class SchoolApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("نظام إدارة المدرسة - Desktop (بسيط ومتين)")
        self.geometry("1000x650")
        # Ensure Arabic right-to-left feel: align labels right, use pack/grid accordingly.
        # Main notebook
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)

        self.students_frame = StudentsFrame(notebook)
        self.teachers_frame = TeachersFrame(notebook)
        self.courses_frame = CoursesFrame(notebook)
        self.enroll_frame = EnrollmentFrame(notebook)
        self.schedule_frame = ScheduleFrame(notebook)
        self.pay_frame = PaymentsFrame(notebook)
        self.report_frame = ReportsFrame(notebook)
        self.backup_frame = BackupFrame(notebook)

        notebook.add(self.students_frame, text="الطلاب")
        notebook.add(self.teachers_frame, text="المعلمين")
        notebook.add(self.courses_frame, text="المواد")
        notebook.add(self.enroll_frame, text="التسجيلات")
        notebook.add(self.schedule_frame, text="الجدول الدراسي")
        notebook.add(self.pay_frame, text="الشؤون المالية")
        notebook.add(self.report_frame, text="التقارير")
        notebook.add(self.backup_frame, text="نسخ / استرجاع")

# ---------- Students Frame ----------
class StudentsFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=10, pady=8)
        ttk.Label(top, text="بحث (رمز/اسم):").pack(side=tk.RIGHT)
        self.search_var = tk.StringVar()
        entry = ttk.Entry(top, textvariable=self.search_var)
        entry.pack(side=tk.RIGHT, padx=5)
        ttk.Button(top, text="بحث", command=self.reload).pack(side=tk.RIGHT, padx=5)
        ttk.Button(top, text="إضافة طالب", command=self.open_add).pack(side=tk.LEFT)
        ttk.Button(top, text="تعديل", command=self.edit_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="حذف", command=self.delete_selected).pack(side=tk.LEFT)

        cols = ("id","code","first_name","last_name","dob","phone","address")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=18)
        headings = ["ID","الرمز","الاسم الأول","اسم العائلة","تاريخ الميلاد","هاتف","عنوان"]
        for c,h in zip(cols,headings):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=100, anchor=tk.CENTER)
        self.tree.column("id",width=50)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.reload()

    def reload(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        txt = self.search_var.get().strip()
        rows = fetch_students(txt if txt else None)
        for r in rows:
            self.tree.insert("",tk.END, values=(r["id"], r["code"], r["first_name"], r["last_name"], r["dob"] or "", r["phone"] or "", r["address"] or ""))

    def open_add(self):
        StudentDialog(self, "إضافة طالب", on_save=lambda d: (add_student(d), self.reload()))

    def edit_selected(self):
        sel = self.tree.selection()
        if not sel: messagebox.showinfo("تنبيه","اختر طالباً أولاً"); return
        vals = self.tree.item(sel[0])["values"]
        sid = vals[0]
        # fetch details
        conn = get_conn(); r = conn.execute("SELECT * FROM students WHERE id=?", (sid,)).fetchone(); conn.close()
        if not r: messagebox.showerror("خطأ","الطالب غير موجود"); return
        data = dict(r)
        StudentDialog(self, "تعديل طالب", data=data, on_save=lambda d: (update_student(sid, d), self.reload()))

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel: messagebox.showinfo("تنبيه","اختر طالباً"); return
        vals = self.tree.item(sel[0])["values"]
        sid = vals[0]
        if messagebox.askyesno("تأكيد","هل تريد حذف الطالب نهائياً؟"):
            delete_student(sid); self.reload()

class StudentDialog(tk.Toplevel):
    def __init__(self, parent, title, data=None, on_save=None):
        super().__init__(parent)
        self.transient(parent); self.grab_set()
        self.title(title)
        self.on_save = on_save
        self.data = data or {}
        frame = ttk.Frame(self); frame.pack(padx=10,pady=10)
        # fields
        labels = [("code","رمز الطالب"),("first_name","الاسم الأول"),("last_name","اسم العائلة"),
                  ("dob","تاريخ الميلاد (YYYY-MM-DD)"),("phone","الهاتف"),("address","العنوان"),("notes","ملاحظات")]
        self.vars = {}
        for key,label in labels:
            row = ttk.Frame(frame); row.pack(fill=tk.X, pady=3)
            ttk.Label(row, text=label, width=25, anchor=tk.E).pack(side=tk.RIGHT)
            v = tk.StringVar(value=self.data.get(key,""))
            ttk.Entry(row, textvariable=v, width=40).pack(side=tk.RIGHT, padx=5)
            self.vars[key]=v
        btn = ttk.Button(frame, text="حفظ", command=self.save); btn.pack(pady=8)
        self.wait_window(self)

    def save(self):
        d = {k: v.get().strip() for k,v in self.vars.items()}
        if not d['code'] or not d['first_name'] or not d['last_name']:
            messagebox.showerror("خطأ","الرجاء تعبئة الرمز والاسم الأول واسم العائلة"); return
        if self.on_save:
            self.on_save(d)
        self.destroy()

# ---------- Teachers Frame ----------
class TeachersFrame(ttk.Frame):
    def __init__(self,parent):
        super().__init__(parent)
        top = ttk.Frame(self); top.pack(fill=tk.X, padx=10, pady=8)
        ttk.Button(top, text="إضافة معلم", command=self.add).pack(side=tk.LEFT)
        ttk.Button(top, text="تعديل", command=self.edit).pack(side=tk.LEFT,padx=5)
        ttk.Button(top, text="حذف", command=self.delete).pack(side=tk.LEFT)

        cols=("id","code","first_name","last_name","phone","subject")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=18)
        heads=["ID","الرمز","الاسم الأول","اسم العائلة","هاتف","المادة"]
        for c,h in zip(cols,heads):
            self.tree.heading(c,text=h); self.tree.column(c,width=120,anchor=tk.CENTER)
        self.tree.column("id",width=50)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.reload()

    def reload(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        for t in fetch_teachers():
            self.tree.insert("",tk.END, values=(t["id"], t["code"], t["first_name"], t["last_name"], t["phone"] or "", t["subject"] or ""))

    def add(self):
        TeacherDialog(self, "إضافة معلم", on_save=lambda d: (add_teacher(d), self.reload()))

    def edit(self):
        sel = self.tree.selection()
        if not sel: messagebox.showinfo("تنبيه","اختر معلم"); return
        vals = self.tree.item(sel[0])["values"]
        tid = vals[0]
        conn = get_conn(); r = conn.execute("SELECT * FROM teachers WHERE id=?", (tid,)).fetchone(); conn.close()
        TeacherDialog(self, "تعديل معلم", data=dict(r), on_save=lambda d: (update_teacher(tid,d), self.reload()))

    def delete(self):
        sel = self.tree.selection()
        if not sel: messagebox.showinfo("تنبيه","اختر معلم"); return
        vals = self.tree.item(sel[0])["values"]
        tid = vals[0]
        if messagebox.askyesno("تأكيد","حذف المعلم؟"):
            delete_teacher(tid); self.reload()

class TeacherDialog(tk.Toplevel):
    def __init__(self,parent,title,data=None,on_save=None):
        super().__init__(parent); self.transient(parent); self.grab_set()
        self.title(title); self.on_save=on_save; self.data=data or {}
        frame=ttk.Frame(self); frame.pack(padx=10,pady=10)
        fields=[("code","رمز المعلم"),("first_name","الاسم الأول"),("last_name","اسم العائلة"),
                ("phone","الهاتف"),("subject","المادة"),("notes","ملاحظات")]
        self.vars={}
        for k,l in fields:
            row=ttk.Frame(frame); row.pack(fill=tk.X,pady=3)
            ttk.Label(row, text=l, width=25, anchor=tk.E).pack(side=tk.RIGHT)
            v=tk.StringVar(value=self.data.get(k,""))
            ttk.Entry(row, textvariable=v, width=40).pack(side=tk.RIGHT, padx=5)
            self.vars[k]=v
        ttk.Button(frame,text="حفظ", command=self.save).pack(pady=6)
        self.wait_window(self)
    def save(self):
        d={k:v.get().strip() for k,v in self.vars.items()}
        if not d['code'] or not d['first_name'] or not d['last_name']:
            messagebox.showerror("خطأ","الرجاء تعبئة الحقول الأساسية"); return
        if self.on_save: self.on_save(d)
        self.destroy()

# ---------- Courses Frame ----------
class CoursesFrame(ttk.Frame):
    def __init__(self,parent):
        super().__init__(parent)
        top=ttk.Frame(self); top.pack(fill=tk.X,padx=10,pady=8)
        ttk.Button(top,text="إضافة مادة", command=self.add).pack(side=tk.LEFT)
        ttk.Button(top,text="تعديل", command=self.edit).pack(side=tk.LEFT,padx=5)
        ttk.Button(top,text="حذف", command=self.delete).pack(side=tk.LEFT)
        cols=("id","code","title","grade_level","fee")
        self.tree=ttk.Treeview(self, columns=cols, show="headings", height=18)
        heads=["ID","الرمز","اسم المادة","الصف/المستوى","رسوم"]
        for c,h in zip(cols,heads):
            self.tree.heading(c,text=h); self.tree.column(c,width=140,anchor=tk.CENTER)
        self.tree.column("id",width=50)
        self.tree.pack(fill=tk.BOTH,expand=True,padx=10,pady=5)
        self.reload()
    def reload(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        for c in fetch_courses():
            self.tree.insert("",tk.END, values=(c["id"], c["code"], c["title"], c["grade_level"] or "", c["fee"] or 0))
    def add(self):
        CourseDialog(self,"إضافة مادة", on_save=lambda d:(add_course(d), self.reload()))
    def edit(self):
        sel=self.tree.selection()
        if not sel: messagebox.showinfo("تنبيه","اختر مادة"); return
        vals=self.tree.item(sel[0])["values"]; cid=vals[0]
        conn=get_conn(); r=conn.execute("SELECT * FROM courses WHERE id=?", (cid,)).fetchone(); conn.close()
        CourseDialog(self,"تعديل مادة", data=dict(r), on_save=lambda d:(update_course(cid,d), self.reload()))
    def delete(self):
        sel=self.tree.selection()
        if not sel: messagebox.showinfo("تنبيه","اختر مادة"); return
        vals=self.tree.item(sel[0])["values"]; cid=vals[0]
        if messagebox.askyesno("تأكيد","حذف المادة؟"):
            delete_course(cid); self.reload()

class CourseDialog(tk.Toplevel):
    def __init__(self,parent,title,data=None,on_save=None):
        super().__init__(parent); self.transient(parent); self.grab_set()
        self.title(title); self.data=data or {}; self.on_save=on_save
        frame=ttk.Frame(self); frame.pack(padx=10,pady=10)
        fields=[("code","رمز المادة"),("title","اسم المادة"),("grade_level","الصف/المستوى"),
                ("fee","الرسوم"),("notes","ملاحظات")]
        self.vars={}
        for k,l in fields:
            row=ttk.Frame(frame); row.pack(fill=tk.X,pady=3)
            ttk.Label(row,text=l, width=25, anchor=tk.E).pack(side=tk.RIGHT)
            v=tk.StringVar(value=self.data.get(k,""))
            ttk.Entry(row,textvariable=v,width=40).pack(side=tk.RIGHT,padx=5)
            self.vars[k]=v
        ttk.Button(frame,text="حفظ",command=self.save).pack(pady=6)
        self.wait_window(self)
    def save(self):
        d={k:(v.get().strip() if k!="fee" else (float(v.get()) if v.get() else 0)) for k,v in self.vars.items()}
        if not d['code'] or not d['title']:
            messagebox.showerror("خطأ","الرجاء تعبئة رمز واسم المادة"); return
        if self.on_save: self.on_save(d)
        self.destroy()

# ---------- Enrollment Frame ----------
class EnrollmentFrame(ttk.Frame):
    def __init__(self,parent):
        super().__init__(parent)
        top=ttk.Frame(self); top.pack(fill=tk.X,padx=10,pady=8)
        ttk.Button(top,text="تسجيل طالب في مادة", command=self.open_enroll).pack(side=tk.LEFT)
        ttk.Button(top,text="حذف تسجيل", command=self.delete_selected).pack(side=tk.LEFT,padx=6)
        cols=("id","student","course","date","status")
        self.tree=ttk.Treeview(self, columns=cols, show="headings", height=20)
        heads=["ID","الطالب","المادة","تاريخ التسجيل","الحالة"]
        for c,h in zip(cols,heads):
            self.tree.heading(c,text=h); self.tree.column(c,width=160,anchor=tk.CENTER)
        self.tree.column("id",width=60)
        self.tree.pack(fill=tk.BOTH,expand=True,padx=10,pady=5)
        self.reload()
    def reload(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        for e in fetch_enrollments():
            self.tree.insert("",tk.END, values=(e["id"], e["student"], e["course"], e["enrollment_date"], e["status"]))
    def open_enroll(self):
        EnrollDialog(self, on_save=lambda s,c:(enroll_student(s,c), self.reload()))
    def delete_selected(self):
        sel=self.tree.selection()
        if not sel: messagebox.showinfo("تنبيه","اختر تسجيل"); return
        eid=self.tree.item(sel[0])["values"][0]
        if messagebox.askyesno("تأكيد","حذف التسجيل؟"):
            delete_enrollment(eid); self.reload()

class EnrollDialog(tk.Toplevel):
    def __init__(self,parent,on_save=None):
        super().__init__(parent); self.transient(parent); self.grab_set()
        self.title("تسجيل طالب"); self.on_save=on_save
        frame=ttk.Frame(self); frame.pack(padx=10,pady=10)
        ttk.Label(frame, text="اختر طالب:").grid(row=0,column=1, sticky=tk.E)
        ttk.Label(frame, text="اختر مادة:").grid(row=1,column=1, sticky=tk.E)
        students = fetch_students()
        courses = fetch_courses()
        self.student_map = {f"{s['code']} | {s['first_name']} {s['last_name']}": s['id'] for s in students}
        self.course_map = {f"{c['code']} | {c['title']}": c['id'] for c in courses}
        self.svar = tk.StringVar()
        self.cvar = tk.StringVar()
        ttk.Combobox(frame, values=list(self.student_map.keys()), textvariable=self.svar, width=50).grid(row=0,column=0,padx=5,pady=4)
        ttk.Combobox(frame, values=list(self.course_map.keys()), textvariable=self.cvar, width=50).grid(row=1,column=0,padx=5,pady=4)
        ttk.Button(frame, text="سجل", command=self.save).grid(row=2,column=0,pady=8)
        self.wait_window(self)
    def save(self):
        s=self.svar.get(); c=self.cvar.get()
        if not s or not c: messagebox.showerror("خطأ","اختر طالبًا والمادة"); return
        if self.on_save: self.on_save(self.student_map[s], self.course_map[c])
        self.destroy()

# ---------- Schedule Frame ----------
class ScheduleFrame(ttk.Frame):
    def __init__(self,parent):
        super().__init__(parent)
        top=ttk.Frame(self); top.pack(fill=tk.X,padx=10,pady=8)
        ttk.Button(top,text="إضافة حصة/جدولة", command=self.add).pack(side=tk.LEFT)
        ttk.Button(top,text="حذف", command=self.delete).pack(side=tk.LEFT,padx=6)
        cols=("id","course","teacher","weekday","time","room")
        self.tree=ttk.Treeview(self, columns=cols, show="headings", height=18)
        heads=["ID","المادة","المعلم","اليوم","الوقت","القاعة"]
        for c,h in zip(cols,heads):
            self.tree.heading(c,text=h); self.tree.column(c,width=140,anchor=tk.CENTER)
        self.tree.column("id",width=60)
        self.tree.pack(fill=tk.BOTH,expand=True,padx=10,pady=5)
        self.reload()
    def reload(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        for s in fetch_schedules():
            time_str = f"{s['start_time'] or ''} - {s['end_time'] or ''}"
            self.tree.insert("",tk.END, values=(s["id"], s["course"], s["teacher"], s["weekday"], time_str, s["room"] or ""))
    def add(self):
        ScheduleDialog(self, on_save=lambda d:(add_schedule(d), self.reload()))
    def delete(self):
        sel=self.tree.selection()
        if not sel: messagebox.showinfo("تنبيه","اختر صفًا"); return
        sid=self.tree.item(sel[0])["values"][0]
        if messagebox.askyesno("تأكيد","حذف الجدولة؟"):
            delete_schedule(sid); self.reload()

class ScheduleDialog(tk.Toplevel):
    def __init__(self,parent,on_save=None):
        super().__init__(parent); self.transient(parent); self.grab_set()
        self.title("إضافة جدول"); self.on_save=on_save
        frame=ttk.Frame(self); frame.pack(padx=10,pady=10)
        courses=fetch_courses(); teachers=fetch_teachers()
        self.course_map={f"{c['code']} | {c['title']}": c['id'] for c in courses}
        self.teacher_map={f"{t['code']} | {t['first_name']} {t['last_name']}": t['id'] for t in teachers}
        ttk.Label(frame,text="المادة:").grid(row=0,column=1,sticky=tk.E); ttk.Label(frame,text="المعلم:").grid(row=1,column=1,sticky=tk.E)
        ttk.Label(frame,text="اليوم:").grid(row=2,column=1,sticky=tk.E); ttk.Label(frame,text="وقت البدء (HH:MM):").grid(row=3,column=1,sticky=tk.E)
        ttk.Label(frame,text="وقت الانتهاء (HH:MM):").grid(row=4,column=1,sticky=tk.E); ttk.Label(frame,text="القاعة:").grid(row=5,column=1,sticky=tk.E)
        self.cvar=tk.StringVar(); self.tvar=tk.StringVar(); self.dayvar=tk.StringVar(); self.startvar=tk.StringVar(); self.endvar=tk.StringVar(); self.roomvar=tk.StringVar()
        ttk.Combobox(frame, values=list(self.course_map.keys()), textvariable=self.cvar, width=50).grid(row=0,column=0,padx=5,pady=3)
        ttk.Combobox(frame, values=list(self.teacher_map.keys()), textvariable=self.tvar, width=50).grid(row=1,column=0,padx=5,pady=3)
        ttk.Combobox(frame, values=["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"], textvariable=self.dayvar, width=50).grid(row=2,column=0,padx=5,pady=3)
        ttk.Entry(frame, textvariable=self.startvar, width=52).grid(row=3,column=0,padx=5,pady=3)
        ttk.Entry(frame, textvariable=self.endvar, width=52).grid(row=4,column=0,padx=5,pady=3)
        ttk.Entry(frame, textvariable=self.roomvar, width=52).grid(row=5,column=0,padx=5,pady=3)
        ttk.Button(frame,text="حفظ", command=self.save).grid(row=6,column=0,pady=8)
        self.wait_window(self)
    def save(self):
        if not self.cvar.get() or not self.tvar.get(): messagebox.showerror("خطأ","اختر مادة ومعلم"); return
        d = {
            "course_id": self.course_map[self.cvar.get()],
            "teacher_id": self.teacher_map[self.tvar.get()],
            "weekday": self.dayvar.get() or "",
            "start_time": self.startvar.get() or "",
            "end_time": self.endvar.get() or "",
            "room": self.roomvar.get() or "",
            "notes": ""
        }
        if self.on_save: self.on_save(d)
        self.destroy()

# ---------- Payments Frame ----------
class PaymentsFrame(ttk.Frame):
    def __init__(self,parent):
        super().__init__(parent)
        top=ttk.Frame(self); top.pack(fill=tk.X,padx=10,pady=8)
        ttk.Button(top,text="تسجيل دفعة", command=self.add).pack(side=tk.LEFT)
        ttk.Button(top,text="تصدير CSV", command=self.export_csv).pack(side=tk.LEFT,padx=6)
        cols=("id","student","amount","method","paid_at")
        self.tree=ttk.Treeview(self, columns=cols, show="headings", height=18)
        heads=["ID","الطالب","المبلغ","الطريقة","التاريخ"]
        for c,h in zip(cols,heads):
            self.tree.heading(c,text=h); self.tree.column(c,width=150,anchor=tk.CENTER)
        self.tree.column("id",width=60)
        self.tree.pack(fill=tk.BOTH,expand=True,padx=10,pady=5)
        self.reload()
    def reload(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        for p in fetch_payments():
            self.tree.insert("",tk.END, values=(p["id"], p["student"] or p["student_code"], p["amount"], p["method"], p["paid_at"]))
    def add(self):
        PaymentDialog(self, on_save=lambda s,a,m,n:(add_payment(s,a,m,n), self.reload()))
    def export_csv(self):
        rows = fetch_payments()
        if not rows: messagebox.showinfo("تنبيه","لا توجد دفعات"); return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")], title="حفظ تقرير الدفعات")
        if not path: return
        with open(path,"w", newline="", encoding="utf-8") as f:
            writer=csv.writer(f)
            writer.writerow(["ID","Student","Amount","Method","PaidAt"])
            for r in rows:
                writer.writerow([r["id"], r["student"] or r["student_code"], r["amount"], r["method"], r["paid_at"]])
        messagebox.showinfo("تم","تم حفظ الملف")

class PaymentDialog(tk.Toplevel):
    def __init__(self,parent,on_save=None):
        super().__init__(parent); self.transient(parent); self.grab_set()
        self.title("تسجيل دفعة"); self.on_save=on_save
        frame=ttk.Frame(self); frame.pack(padx=10,pady=10)
        ttk.Label(frame,text="اختر طالب:").grid(row=0,column=1,sticky=tk.E); ttk.Label(frame,text="المبلغ:").grid(row=1,column=1,sticky=tk.E)
        ttk.Label(frame,text="الطريقة:").grid(row=2,column=1,sticky=tk.E); ttk.Label(frame,text="ملاحظة:").grid(row=3,column=1,sticky=tk.E)
        students = fetch_students()
        self.st_map = {f"{s['code']} | {s['first_name']} {s['last_name']}": s['id'] for s in students}
        self.svar=tk.StringVar(); self.amt=tk.StringVar(); self.method=tk.StringVar(value="نقداً"); self.note=tk.StringVar()
        ttk.Combobox(frame, values=list(self.st_map.keys()), textvariable=self.svar, width=50).grid(row=0,column=0,padx=5,pady=3)
        ttk.Entry(frame, textvariable=self.amt, width=52).grid(row=1,column=0,padx=5,pady=3)
        ttk.Combobox(frame, values=["نقداً","بطاقة","تحويل"], textvariable=self.method, width=50).grid(row=2,column=0,padx=5,pady=3)
        ttk.Entry(frame, textvariable=self.note, width=52).grid(row=3,column=0,padx=5,pady=3)
        ttk.Button(frame,text="حفظ", command=self.save).grid(row=4,column=0,pady=8)
        self.wait_window(self)
    def save(self):
        if not self.svar.get() or not self.amt.get(): messagebox.showerror("خطأ","اختر طالبًا وادخل المبلغ"); return
        try:
            a=float(self.amt.get())
        except:
            messagebox.showerror("خطأ","المبلغ غير صحيح"); return
        if self.on_save: self.on_save(self.st_map[self.svar.get()], a, self.method.get(), self.note.get())
        self.destroy()

# ---------- Reports Frame ----------
class ReportsFrame(ttk.Frame):
    def __init__(self,parent):
        super().__init__(parent)
        top=ttk.Frame(self); top.pack(fill=tk.X,padx=10,pady=8)
        ttk.Button(top,text="تقرير الطلاب (CSV)", command=self.export_students).pack(side=tk.LEFT)
        ttk.Button(top,text="ملخص مالي", command=self.show_finance).pack(side=tk.LEFT,padx=6)
        self.txt = tk.Text(self, wrap=tk.WORD); self.txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.show_finance()

    def export_students(self):
        rows = fetch_students()
        if not rows: messagebox.showinfo("تنبيه","لا يوجد طلاب"); return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")], title="حفظ تقرير الطلاب")
        if not path: return
        with open(path,"w", newline="", encoding="utf-8") as f:
            writer=csv.writer(f)
            writer.writerow(["ID","Code","First","Last","DOB","Phone","Address"])
            for s in rows:
                writer.writerow([s["id"], s["code"], s["first_name"], s["last_name"], s["dob"], s["phone"], s["address"]])
        messagebox.showinfo("تم","تم حفظ الملف")

    def show_finance(self):
        s = finance_summary()
        self.txt.delete("1.0", tk.END)
        self.txt.insert(tk.END, f"ملخص مالي\n\nإجمالي المبالغ المسجلة: {s.get('total',0)}\nعدد الدفعات: {s.get('count',0)}\n\n")
        self.txt.insert(tk.END, "ملاحظات:\n- لتفاصيل أكثر استخدم تصدير الدفعات في تبويب الشؤون المالية.\n")

# ---------- Backup Frame ----------
class BackupFrame(ttk.Frame):
    def __init__(self,parent):
        super().__init__(parent)
        frame=ttk.Frame(self); frame.pack(padx=10,pady=10)
        ttk.Button(frame,text="انشاء نسخة احتياطية الآن", command=self.backup).grid(row=0,column=0,padx=6,pady=6)
        ttk.Button(frame,text="استرجاع نسخة", command=self.restore).grid(row=0,column=1,padx=6,pady=6)
        ttk.Button(frame,text="فتح مجلد النسخ الاحتياطي", command=self.open_backups).grid(row=1,column=0,padx=6,pady=6)
        ttk.Label(frame,text=f"مجلد النسخ: {BACKUP_DIR}").grid(row=2,column=0,columnspan=2,sticky=tk.W,pady=8)

    def backup(self):
        dest = make_backup()
        messagebox.showinfo("تم","تم إنشاء نسخة احتياطية:\n" + dest)

    def restore(self):
        path = filedialog.askopenfilename(initialdir=BACKUP_DIR, title="اختر ملف نسخة لاسترجاعه", filetypes=[("DB files","*.db"),("All files","*.*")])
        if not path: return
        if messagebox.askyesno("تأكيد","استرجاع النسخة سيستبدل قاعدة البيانات الحالية. متابعة؟"):
            try:
                restore_backup(path)
                messagebox.showinfo("تم","تم الاسترجاع. أعد تشغيل التطبيق لرؤية التغييرات.")
            except Exception as e:
                messagebox.showerror("خطأ", str(e))

    def open_backups(self):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        try:
            if os.name == "nt":
                os.startfile(BACKUP_DIR)
            else:
                import subprocess
                subprocess.Popen(["xdg-open", BACKUP_DIR])
        except Exception as e:
            messagebox.showerror("خطأ", str(e))

# -----------------------
# Run app
# -----------------------
if __name__ == "__main__":
    init_db()
    app = SchoolApp()
    app.mainloop()
