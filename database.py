"""
Database module for Face Recognition Attendance System.
Handles SQLite database initialization, student CRUD, and attendance operations.
"""

import sqlite3
import os
import json
import numpy as np
from datetime import datetime, date
import calendar

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'attendance.db')

# ─── Branch Code Mapping (from Registration Number) ─────────────
# Registration Number Format: YYBBBFFFXXXXX (exactly 11 digits)
#   YY   = Admission Year (e.g., 21 = 2021, valid: 19-current year)
#   BBB  = Branch Code (e.g., 103 = EE)
#   FFF  = Fixed compulsory digits: 135
#   XXXXX= Student Roll Number
BRANCH_CODES = {
    '101': 'CE',
    '102': 'ME',
    '103': 'EE',
    '104': 'ECE',
    '105': 'CSE',
    '106': 'IT',
    '107': 'EEE',
}

# Valid admission years (2019 to current year)
VALID_YEAR_RANGE = range(19, int(str(date.today().year)[2:]) + 1)


def validate_reg_number(reg_number):
    """
    Validate registration number format: YYBBB135XXXXX (11 digits).
    Returns (is_valid, error_message, detected_branch).
    """
    if not reg_number.isdigit():
        return False, "Registration number must contain only digits.", None

    if len(reg_number) != 11:
        return False, f"Registration number must be exactly 11 digits (e.g., 21103135014). You entered {len(reg_number)} digits.", None

    year_part = reg_number[0:2]
    branch_code = reg_number[2:5]
    fixed_part = reg_number[5:8]
    roll_part = reg_number[8:]

    # Validate year (must be between 19 and current year's last 2 digits)
    year_int = int(year_part)
    if year_int not in VALID_YEAR_RANGE:
        valid_years = f"{min(VALID_YEAR_RANGE)}-{max(VALID_YEAR_RANGE)}"
        return False, f"Invalid admission year '{year_part}'. Year must be between {valid_years} (e.g., 21 for 2021).", None

    # Validate branch code
    if branch_code not in BRANCH_CODES:
        valid_codes = ', '.join([f"{k}={v}" for k, v in BRANCH_CODES.items()])
        return False, f"Invalid branch code '{branch_code}'. Valid codes: {valid_codes}.", None

    # Validate fixed part (must be 135)
    if fixed_part != '135':
        return False, f"Digits 6-8 must be '135' (compulsory). You entered '{fixed_part}'.", None

    detected_branch = BRANCH_CODES[branch_code]
    return True, "Valid registration number.", detected_branch


def get_branch_from_reg(reg_number):
    """Extract branch from registration number using branch code (digits 3-5)."""
    if len(reg_number) >= 5 and reg_number.isdigit():
        code = reg_number[2:5]
        return BRANCH_CODES.get(code, None)
    return None


def get_db():
    """Get a database connection with row_factory enabled."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database tables."""
    conn = get_db()
    cursor = conn.cursor()

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
    conn.close()


# ═══════════════════════════════════════════════════════════════
#  CREATE
# ═══════════════════════════════════════════════════════════════

def add_student(name, reg_number, dob, phone, branch, face_encoding):
    """Add a new student to the database."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        encoding_json = json.dumps(face_encoding.tolist())
        normalized_dob = normalize_dob(dob)
        cursor.execute(
            'INSERT INTO students (name, reg_number, dob, phone, branch, face_encoding) VALUES (?, ?, ?, ?, ?, ?)',
            (name, reg_number, normalized_dob, phone, branch, encoding_json)
        )
        conn.commit()
        return True, "Student registered successfully!"
    except sqlite3.IntegrityError:
        return False, "DUPLICATE"
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        conn.close()


def mark_attendance(student_id):
    """Mark attendance for a student. Prevents duplicate attendance on the same day."""
    conn = get_db()
    cursor = conn.cursor()
    today = date.today().isoformat()

    try:
        cursor.execute(
            'INSERT INTO attendance (student_id, date) VALUES (?, ?)',
            (student_id, today)
        )
        conn.commit()
        return True, "Attendance marked successfully!"
    except sqlite3.IntegrityError:
        return False, "Attendance already marked for today!"
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════
#  READ
# ═══════════════════════════════════════════════════════════════

def get_student_by_reg(reg_number):
    """Get a student by registration number."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students WHERE reg_number = ?', (reg_number,))
    student = cursor.fetchone()
    conn.close()
    return student


def get_student_by_id(student_id):
    """Get a student by ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
    student = cursor.fetchone()
    conn.close()
    return student


def get_all_students():
    """Get all students."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students ORDER BY branch, name')
    students = cursor.fetchall()
    conn.close()
    return students


def get_students_by_branch(branch):
    """Get students filtered by branch."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM students WHERE branch = ? ORDER BY name', (branch,))
    students = cursor.fetchall()
    conn.close()
    return students


def get_all_branches():
    """Get all unique branches."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT branch FROM students ORDER BY branch')
    branches = [row['branch'] for row in cursor.fetchall()]
    conn.close()
    return branches


def check_attendance_today(student_id):
    """Check if attendance is already marked for today."""
    conn = get_db()
    cursor = conn.cursor()
    today = date.today().isoformat()
    cursor.execute(
        'SELECT * FROM attendance WHERE student_id = ? AND date = ?',
        (student_id, today)
    )
    record = cursor.fetchone()
    conn.close()
    return record is not None


def get_attendance_count(student_id):
    """Get the total attendance count for a student in the current month."""
    conn = get_db()
    cursor = conn.cursor()
    today = date.today()
    first_day = today.replace(day=1).isoformat()
    last_day = today.isoformat()

    cursor.execute(
        'SELECT COUNT(*) as count FROM attendance WHERE student_id = ? AND date BETWEEN ? AND ?',
        (student_id, first_day, last_day)
    )
    result = cursor.fetchone()
    conn.close()
    return result['count']


def get_attendance_history(student_id):
    """Get full attendance history for a student, ordered by date descending."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT date, timestamp FROM attendance WHERE student_id = ? ORDER BY date DESC',
        (student_id,)
    )
    records = cursor.fetchall()
    conn.close()
    return [{'date': r['date'], 'timestamp': r['timestamp']} for r in records]


def get_all_face_encodings():
    """Get all face encodings from the database for matching."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, reg_number, branch, face_encoding FROM students')
    students = cursor.fetchall()
    conn.close()

    result = []
    for s in students:
        encoding = np.array(json.loads(s['face_encoding']))
        result.append({
            'id': s['id'],
            'name': s['name'],
            'reg_number': s['reg_number'],
            'branch': s['branch'],
            'encoding': encoding
        })
    return result


# ═══════════════════════════════════════════════════════════════
#  UPDATE
# ═══════════════════════════════════════════════════════════════

def update_student(student_id, name, phone, branch):
    """Update a student's editable fields (name, phone, branch)."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'UPDATE students SET name = ?, phone = ?, branch = ? WHERE id = ?',
            (name, phone, branch, student_id)
        )
        conn.commit()
        if cursor.rowcount == 0:
            return False, "Student not found!"
        return True, "Student updated successfully!"
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════
#  DELETE
# ═══════════════════════════════════════════════════════════════

def delete_student(student_id):
    """Delete a student and their attendance records."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM attendance WHERE student_id = ?', (student_id,))
        cursor.execute('DELETE FROM students WHERE id = ?', (student_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return False, "Student not found!"
        return True, "Student deleted successfully!"
    except Exception as e:
        return False, f"Error: {str(e)}"
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════
#  CALCULATIONS
# ═══════════════════════════════════════════════════════════════

def get_working_days_in_month():
    """Calculate working days in current month UP TO TODAY (not future days)."""
    today = date.today()
    year = today.year
    month = today.month

    sundays = 0
    for day in range(1, today.day + 1):
        if date(year, month, day).weekday() == 6:
            sundays += 1

    return today.day - sundays


def get_attendance_percentage(student_id):
    """Calculate attendance percentage for the current month."""
    present_days = get_attendance_count(student_id)
    working_days = get_working_days_in_month()
    if working_days == 0:
        return 0.0
    return round((present_days / working_days) * 100, 2)


def get_admin_dashboard_data(branch_filter=None):
    """Get dashboard data with ALL student details using efficient JOIN."""
    conn = get_db()
    cursor = conn.cursor()

    today = date.today()
    first_day = today.replace(day=1).isoformat()
    last_day = today.isoformat()
    working_days = get_working_days_in_month()

    if branch_filter and branch_filter != 'all':
        cursor.execute('''
            SELECT s.id, s.name, s.branch, s.reg_number, s.dob, s.phone, s.created_at,
                   COUNT(a.id) as present_days
            FROM students s
            LEFT JOIN attendance a ON s.id = a.student_id
                AND a.date BETWEEN ? AND ?
            WHERE s.branch = ?
            GROUP BY s.id
            ORDER BY s.name
        ''', (first_day, last_day, branch_filter))
    else:
        cursor.execute('''
            SELECT s.id, s.name, s.branch, s.reg_number, s.dob, s.phone, s.created_at,
                   COUNT(a.id) as present_days
            FROM students s
            LEFT JOIN attendance a ON s.id = a.student_id
                AND a.date BETWEEN ? AND ?
            GROUP BY s.id
            ORDER BY s.branch, s.name
        ''', (first_day, last_day))

    students = cursor.fetchall()
    conn.close()

    dashboard_data = []
    for student in students:
        present = student['present_days']
        percentage = round((present / working_days) * 100, 2) if working_days > 0 else 0.0

        dashboard_data.append({
            'id': student['id'],
            'name': student['name'],
            'branch': student['branch'],
            'reg_number': student['reg_number'],
            'dob': student['dob'],
            'phone': student['phone'],
            'created_at': student['created_at'],
            'present_days': present,
            'working_days': working_days,
            'percentage': percentage
        })

    return dashboard_data


# ═══════════════════════════════════════════════════════════════
#  UTILITIES
# ═══════════════════════════════════════════════════════════════

def normalize_dob(dob_string):
    """Normalize DOB to YYYY-MM-DD format regardless of input format."""
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d/%m/%Y'):
        try:
            parsed = datetime.strptime(dob_string, fmt)
            return parsed.strftime('%Y-%m-%d')
        except ValueError:
            continue
    return dob_string


def validate_dob_age(dob_string, min_age=18):
    """Validate that the person is at least min_age years old."""
    normalized = normalize_dob(dob_string)
    try:
        dob_date = datetime.strptime(normalized, '%Y-%m-%d').date()
        today = date.today()
        age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))

        if age < min_age:
            return False, f"You must be at least {min_age} years old to register. Your age: {age} years."

        if age > 100:
            return False, "Invalid date of birth. Please enter a valid date."

        if dob_date > today:
            return False, "Date of birth cannot be in the future."

        return True, "Valid date of birth."
    except (ValueError, TypeError):
        return False, "Invalid date format. Please use the date picker."


def validate_phone(phone):
    """Validate Indian phone number format (must start with 6/7/8/9, exactly 10 digits)."""
    if not phone.isdigit():
        return False, "Phone number must contain only digits."

    if len(phone) != 10:
        return False, "Phone number must be exactly 10 digits."

    if phone[0] not in ('6', '7', '8', '9'):
        return False, "Invalid phone number. Indian numbers must start with 6, 7, 8, or 9."

    return True, "Valid phone number."
