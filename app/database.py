import psycopg2
from psycopg2.extras import DictCursor
import os
import json
import numpy as np
from datetime import datetime, date

DATABASE_URL = os.environ.get('DATABASE_URL')

BRANCH_CODES = {
    '101': 'CE', '102': 'ME', '103': 'EE', '104': 'ECE', '105': 'CSE', '106': 'IT', '107': 'EEE',
}
VALID_YEAR_RANGE = range(19, int(str(date.today().year)[2:]) + 1)

def validate_reg_number(reg_number):
    if not reg_number.isdigit(): return False, "Registration number must contain only digits.", None
    if len(reg_number) != 11: return False, f"Must be exactly 11 digits.", None
    year_part, branch_code, fixed_part = reg_number[0:2], reg_number[2:5], reg_number[5:8]
    if int(year_part) not in VALID_YEAR_RANGE: return False, "Invalid admission year.", None
    if branch_code not in BRANCH_CODES: return False, "Invalid branch code.", None
    if fixed_part != '135': return False, "Digits 6-8 must be '135'.", None
    return True, "Valid.", BRANCH_CODES[branch_code]

def get_branch_from_reg(reg_number):
    if len(reg_number) >= 5 and reg_number.isdigit():
        return BRANCH_CODES.get(reg_number[2:5], None)
    return None

def get_db():
    if not DATABASE_URL:
        # Fallback to sqlite if postgres is not provided (helps local dev if they didn't set it yet)
        import sqlite3
        conn = sqlite3.connect('attendance.db')
        conn.row_factory = sqlite3.Row
        return conn
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    try:
        if DATABASE_URL:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    reg_number TEXT NOT NULL UNIQUE,
                    dob TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    branch TEXT NOT NULL,
                    face_encoding TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id SERIAL PRIMARY KEY,
                    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
                    date TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(student_id, date)
                )
            ''')
        else:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    reg_number TEXT NOT NULL UNIQUE,
                    dob TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    branch TEXT NOT NULL,
                    face_encoding TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                    UNIQUE(student_id, date)
                )
            ''')
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Init DB Warning (Expected with multiple Gunicorn workers): {e}")
    finally:
        conn.close()

def add_student(name, reg_number, dob, phone, branch, face_encoding):
    conn = get_db()
    cursor = conn.cursor()
    try:
        encoding_json = json.dumps(face_encoding.tolist())
        query = 'INSERT INTO students (name, reg_number, dob, phone, branch, face_encoding) VALUES (%s, %s, %s, %s, %s, %s)' if DATABASE_URL else 'INSERT INTO students (name, reg_number, dob, phone, branch, face_encoding) VALUES (?, ?, ?, ?, ?, ?)'
        cursor.execute(query, (name, reg_number, normalize_dob(dob), phone, branch, encoding_json))
        conn.commit()
        return True, "Student registered successfully!"
    except Exception as e:
        if 'UNIQUE' in str(e).upper() or 'DUPLICATE' in str(e).upper(): return False, "DUPLICATE"
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def mark_attendance(student_id):
    conn = get_db()
    cursor = conn.cursor()
    today = date.today().isoformat()
    try:
        query = 'INSERT INTO attendance (student_id, date) VALUES (%s, %s)' if DATABASE_URL else 'INSERT INTO attendance (student_id, date) VALUES (?, ?)'
        cursor.execute(query, (student_id, today))
        conn.commit()
        return True, "Attendance marked successfully!"
    except Exception as e:
        if 'UNIQUE' in str(e).upper() or 'DUPLICATE' in str(e).upper(): return False, "Attendance already marked for today!"
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def get_student_by_reg(reg_number):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=DictCursor) if DATABASE_URL else conn.cursor()
    query = 'SELECT * FROM students WHERE reg_number = %s' if DATABASE_URL else 'SELECT * FROM students WHERE reg_number = ?'
    cursor.execute(query, (reg_number,))
    student = cursor.fetchone()
    conn.close()
    return dict(student) if student else None

def get_student_by_id(student_id):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=DictCursor) if DATABASE_URL else conn.cursor()
    query = 'SELECT * FROM students WHERE id = %s' if DATABASE_URL else 'SELECT * FROM students WHERE id = ?'
    cursor.execute(query, (student_id,))
    student = cursor.fetchone()
    conn.close()
    return dict(student) if student else None

def get_all_students():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=DictCursor) if DATABASE_URL else conn.cursor()
    cursor.execute('SELECT * FROM students ORDER BY branch, name')
    students = cursor.fetchall()
    conn.close()
    return [dict(s) for s in students]

def get_students_by_branch(branch):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=DictCursor) if DATABASE_URL else conn.cursor()
    query = 'SELECT * FROM students WHERE branch = %s ORDER BY name' if DATABASE_URL else 'SELECT * FROM students WHERE branch = ? ORDER BY name'
    cursor.execute(query, (branch,))
    students = cursor.fetchall()
    conn.close()
    return [dict(s) for s in students]

def get_all_branches():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=DictCursor) if DATABASE_URL else conn.cursor()
    cursor.execute('SELECT DISTINCT branch FROM students ORDER BY branch')
    branches = [row['branch'] for row in cursor.fetchall()]
    conn.close()
    return branches

def check_attendance_today(student_id):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=DictCursor) if DATABASE_URL else conn.cursor()
    query = 'SELECT * FROM attendance WHERE student_id = %s AND date = %s' if DATABASE_URL else 'SELECT * FROM attendance WHERE student_id = ? AND date = ?'
    cursor.execute(query, (student_id, date.today().isoformat()))
    record = cursor.fetchone()
    conn.close()
    return record is not None

def get_attendance_count(student_id):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=DictCursor) if DATABASE_URL else conn.cursor()
    today = date.today()
    query = 'SELECT COUNT(*) as count FROM attendance WHERE student_id = %s AND date BETWEEN %s AND %s' if DATABASE_URL else 'SELECT COUNT(*) as count FROM attendance WHERE student_id = ? AND date BETWEEN ? AND ?'
    cursor.execute(query, (student_id, today.replace(day=1).isoformat(), today.isoformat()))
    result = cursor.fetchone()
    conn.close()
    return result['count']

def get_attendance_history(student_id):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=DictCursor) if DATABASE_URL else conn.cursor()
    query = 'SELECT date, timestamp FROM attendance WHERE student_id = %s ORDER BY date DESC' if DATABASE_URL else 'SELECT date, timestamp FROM attendance WHERE student_id = ? ORDER BY date DESC'
    cursor.execute(query, (student_id,))
    records = cursor.fetchall()
    conn.close()
    return [{'date': r['date'], 'timestamp': r['timestamp']} for r in records]

def get_all_face_encodings():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=DictCursor) if DATABASE_URL else conn.cursor()
    cursor.execute('SELECT id, name, reg_number, branch, face_encoding FROM students')
    students = cursor.fetchall()
    conn.close()
    return [{'id': s['id'], 'name': s['name'], 'reg_number': s['reg_number'], 'branch': s['branch'], 'encoding': np.array(json.loads(s['face_encoding']))} for s in students]

def update_student(student_id, name, phone, branch):
    conn = get_db()
    cursor = conn.cursor()
    try:
        query = 'UPDATE students SET name = %s, phone = %s, branch = %s WHERE id = %s' if DATABASE_URL else 'UPDATE students SET name = ?, phone = ?, branch = ? WHERE id = ?'
        cursor.execute(query, (name, phone, branch, student_id))
        conn.commit()
        return (True, "Student updated successfully!") if cursor.rowcount > 0 else (False, "Student not found!")
    except Exception as e: return False, f"Error: {str(e)}"
    finally: conn.close()

def delete_student(student_id):
    conn = get_db()
    cursor = conn.cursor()
    try:
        query1 = 'DELETE FROM attendance WHERE student_id = %s' if DATABASE_URL else 'DELETE FROM attendance WHERE student_id = ?'
        query2 = 'DELETE FROM students WHERE id = %s' if DATABASE_URL else 'DELETE FROM students WHERE id = ?'
        cursor.execute(query1, (student_id,))
        cursor.execute(query2, (student_id,))
        conn.commit()
        return (True, "Student deleted successfully!") if cursor.rowcount > 0 else (False, "Student not found!")
    except Exception as e: return False, f"Error: {str(e)}"
    finally: conn.close()

def get_working_days_in_month():
    today = date.today()
    sundays = sum(1 for day in range(1, today.day + 1) if date(today.year, today.month, day).weekday() == 6)
    return today.day - sundays

def get_attendance_percentage(student_id):
    working_days = get_working_days_in_month()
    return round((get_attendance_count(student_id) / working_days) * 100, 2) if working_days > 0 else 0.0

def get_admin_dashboard_data(branch_filter=None):
    conn = get_db()
    cursor = conn.cursor(cursor_factory=DictCursor) if DATABASE_URL else conn.cursor()
    first_day, last_day = date.today().replace(day=1).isoformat(), date.today().isoformat()
    working_days = get_working_days_in_month()

    query_base = '''
        SELECT s.id, s.name, s.branch, s.reg_number, s.dob, s.phone, s.created_at, COUNT(a.id) as present_days
        FROM students s LEFT JOIN attendance a ON s.id = a.student_id AND a.date BETWEEN {p1} AND {p2}
    '''
    
    p = '%s' if DATABASE_URL else '?'
    query = query_base.format(p1=p, p2=p)

    if branch_filter and branch_filter != 'all':
        cursor.execute(query + f' WHERE s.branch = {p} GROUP BY s.id ORDER BY s.name', (first_day, last_day, branch_filter))
    else:
        cursor.execute(query + ' GROUP BY s.id ORDER BY s.branch, s.name', (first_day, last_day))
    
    students = cursor.fetchall()
    conn.close()
    
    return [{
        **dict(s), 'working_days': working_days,
        'percentage': round((s['present_days'] / working_days) * 100, 2) if working_days > 0 else 0.0
    } for s in students]

def normalize_dob(dob_string):
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y'):
        try: return datetime.strptime(dob_string, fmt).strftime('%Y-%m-%d')
        except ValueError: continue
    return dob_string

def validate_dob_age(dob_string, min_age=18):
    try:
        dob_date = datetime.strptime(normalize_dob(dob_string), '%Y-%m-%d').date()
        today = date.today()
        age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
        if age < min_age: return False, f"Must be at least {min_age} years old."
        if dob_date > today: return False, "DOB cannot be future."
        return True, "Valid."
    except: return False, "Invalid format."

def validate_phone(phone):
    if not phone.isdigit() or len(phone) != 10 or phone[0] not in '6789': return False, "Invalid Indian phone number."
    return True, "Valid."
