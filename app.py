"""
Face Recognition-Based Attendance System
Main Flask Application
"""

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from database import (
    init_db, add_student, get_student_by_reg, get_student_by_id,
    mark_attendance, check_attendance_today,
    get_attendance_count, get_working_days_in_month,
    get_attendance_percentage, get_all_branches,
    get_admin_dashboard_data, get_attendance_history,
    update_student, delete_student,
    get_branch_from_reg, normalize_dob, BRANCH_CODES,
    validate_reg_number, validate_dob_age, validate_phone
)
from face_utils import encode_face_from_base64, match_face
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Admin credentials
ADMIN_USERNAME = 'subham'
ADMIN_PASSWORD = 'admin@1234'


# ─── Landing Page ───────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


# ─── Student Registration ──────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        name = data.get('name', '').strip()
        reg_number = data.get('reg_number', '').strip()
        dob = data.get('dob', '').strip()
        phone = data.get('phone', '').strip()
        branch = data.get('branch', '').strip()
        face_image = data.get('face_image', '')

        # ── All fields required ──
        if not all([name, reg_number, dob, phone, branch, face_image]):
            return jsonify({'success': False, 'message': 'All fields are required!'})

        # ── Name validation ──
        if not name.replace(' ', '').isalpha():
            return jsonify({'success': False, 'message': 'Enter only alphabets in Name (e.g., Ram)'})

        # ── Registration Number: strict 11-digit format ──
        is_valid, reg_msg, detected_branch = validate_reg_number(reg_number)
        if not is_valid:
            return jsonify({'success': False, 'message': reg_msg})

        # Verify branch matches the registration number code
        if detected_branch != branch:
            return jsonify({
                'success': False,
                'message': f'Branch mismatch! Your registration number indicates "{detected_branch}" branch (code {reg_number[2:5]}), but you selected "{branch}". Please correct the branch.'
            })

        # ── Check if already registered ──
        existing = get_student_by_reg(reg_number)
        if existing:
            return jsonify({
                'success': False,
                'message': f'This registration number ({reg_number}) is already registered under the name "{existing["name"]}". Kindly go to Student Login and login with your credentials (Registration Number + Date of Birth).',
                'already_registered': True
            })

        # ── DOB: must be 18+ years old ──
        dob_valid, dob_msg = validate_dob_age(dob)
        if not dob_valid:
            return jsonify({'success': False, 'message': dob_msg})

        # ── Phone: Indian format, starts with 6/7/8/9 ──
        phone_valid, phone_msg = validate_phone(phone)
        if not phone_valid:
            return jsonify({'success': False, 'message': phone_msg})

        # ── Encode face ──
        encoding, msg = encode_face_from_base64(face_image)
        if encoding is None:
            return jsonify({'success': False, 'message': msg})

        # ── Save to database ──
        success, message = add_student(name, reg_number, dob, phone, branch, encoding)

        if not success and message == "DUPLICATE":
            return jsonify({
                'success': False,
                'message': f'This registration number is already registered. Kindly go to Student Login and login with your credentials.',
                'already_registered': True
            })

        return jsonify({'success': success, 'message': message})

    return render_template('register.html', branch_codes=BRANCH_CODES)


# ─── Validate Registration Number (AJAX) ───────────────────────
@app.route('/api/validate_reg', methods=['POST'])
def api_validate_reg():
    """Real-time registration number validation API."""
    data = request.get_json()
    reg_number = data.get('reg_number', '').strip()

    if not reg_number:
        return jsonify({'valid': False, 'message': ''})

    # Check if only digits
    if not reg_number.isdigit():
        return jsonify({'valid': False, 'message': 'Only numeric digits allowed.'})

    # Check if complete (11 digits)
    if len(reg_number) < 11:
        # Partial — give hints
        hints = []
        if len(reg_number) >= 2:
            year = reg_number[0:2]
            from database import VALID_YEAR_RANGE
            if int(year) not in VALID_YEAR_RANGE:
                return jsonify({'valid': False, 'message': f'Invalid year "{year}". Must be {min(VALID_YEAR_RANGE)}-{max(VALID_YEAR_RANGE)}.'})
        if len(reg_number) >= 5:
            code = reg_number[2:5]
            if code not in BRANCH_CODES:
                return jsonify({'valid': False, 'message': f'Invalid branch code "{code}". Valid: 101-107.'})
            else:
                branch = BRANCH_CODES[code]
                return jsonify({'valid': False, 'message': f'Branch: {branch}. Keep typing... ({len(reg_number)}/11 digits)', 'branch': branch})

        return jsonify({'valid': False, 'message': f'Keep typing... ({len(reg_number)}/11 digits)'})

    if len(reg_number) > 11:
        return jsonify({'valid': False, 'message': f'Too many digits! Must be exactly 11. You entered {len(reg_number)}.'})

    # Full validation
    is_valid, msg, branch = validate_reg_number(reg_number)

    # Check if already registered
    if is_valid:
        existing = get_student_by_reg(reg_number)
        if existing:
            return jsonify({
                'valid': False,
                'message': f'Already registered under "{existing["name"]}". Please login instead.',
                'already_registered': True,
                'branch': branch
            })

    return jsonify({'valid': is_valid, 'message': msg, 'branch': branch if is_valid else None})


# ─── Get Branch from Reg Number (AJAX) ─────────────────────────
@app.route('/api/detect_branch', methods=['POST'])
def detect_branch():
    data = request.get_json()
    reg_number = data.get('reg_number', '').strip()
    branch = get_branch_from_reg(reg_number)
    if branch:
        return jsonify({'success': True, 'branch': branch})
    return jsonify({'success': False})


# ─── Student Login ──────────────────────────────────────────────
@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        reg_number = request.form.get('reg_number', '').strip()
        dob = request.form.get('dob', '').strip()

        normalized_dob = normalize_dob(dob)

        student = get_student_by_reg(reg_number)
        if student and student['dob'] == normalized_dob:
            session.pop('is_admin', None)
            session.pop('admin_name', None)

            session['student_id'] = student['id']
            session['student_name'] = student['name']
            session['student_reg'] = student['reg_number']
            session['student_branch'] = student['branch']
            session['is_student'] = True
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid Registration Number or Date of Birth!', 'danger')

    return render_template('student_login.html')


# ─── Forgot Credentials (Face-Based Recovery) ──────────────────
@app.route('/student/forgot', methods=['GET'])
def forgot_credentials():
    return render_template('forgot_credentials.html')


@app.route('/student/forgot/verify', methods=['POST'])
def forgot_verify_face():
    """Verify face and return student credentials."""
    data = request.get_json()
    face_image = data.get('face_image', '')

    if not face_image:
        return jsonify({'success': False, 'message': 'No face image provided!'})

    # Match face against database
    matched, msg = match_face(face_image)
    if matched is None:
        return jsonify({'success': False, 'message': msg})

    # Get full student details
    student = get_student_by_id(matched['id'])
    if not student:
        return jsonify({'success': False, 'message': 'Student record not found.'})

    # Return credentials (DOB partially masked for display, full for auto-fill)
    dob = student['dob']  # YYYY-MM-DD
    dob_display = f"{dob[:4]}-**-{dob[8:]}"  # Show year and day, mask month

    return jsonify({
        'success': True,
        'message': f'Face matched with {matched["confidence"]}% confidence!',
        'name': student['name'],
        'reg_number': student['reg_number'],
        'branch': student['branch'],
        'dob_display': dob_display,
        'dob_full': dob,
        'confidence': matched['confidence']
    })


# ─── Student Dashboard ─────────────────────────────────────────
@app.route('/student/dashboard')
def student_dashboard():
    if not session.get('is_student'):
        flash('Please login first!', 'warning')
        return redirect(url_for('student_login'))

    student_id = session['student_id']
    already_marked = check_attendance_today(student_id)
    present_days = get_attendance_count(student_id)
    working_days = get_working_days_in_month()
    percentage = get_attendance_percentage(student_id)

    return render_template('student_dashboard.html',
                           already_marked=already_marked,
                           present_days=present_days,
                           working_days=working_days,
                           percentage=percentage)


# ─── Student Attendance History ─────────────────────────────────
@app.route('/student/history')
def student_history():
    if not session.get('is_student'):
        flash('Please login first!', 'warning')
        return redirect(url_for('student_login'))

    student_id = session['student_id']
    history = get_attendance_history(student_id)
    present_days = get_attendance_count(student_id)
    working_days = get_working_days_in_month()
    percentage = get_attendance_percentage(student_id)

    return render_template('student_history.html',
                           history=history,
                           present_days=present_days,
                           working_days=working_days,
                           percentage=percentage)


# ─── Mark Attendance (AJAX) ────────────────────────────────────
@app.route('/student/mark_attendance', methods=['POST'])
def mark_attendance_route():
    if not session.get('is_student'):
        return jsonify({'success': False, 'message': 'Please login first!'})

    data = request.get_json()
    face_image = data.get('face_image', '')

    if not face_image:
        return jsonify({'success': False, 'message': 'No face image provided!'})

    matched, msg = match_face(face_image)
    if matched is None:
        return jsonify({'success': False, 'message': msg})

    if matched['id'] != session['student_id']:
        return jsonify({
            'success': False,
            'message': 'Face does not match the logged-in student!'
        })

    success, message = mark_attendance(session['student_id'])

    if success:
        present_days = get_attendance_count(session['student_id'])
        working_days = get_working_days_in_month()
        percentage = get_attendance_percentage(session['student_id'])
        return jsonify({
            'success': True,
            'message': message,
            'student_name': session['student_name'],
            'branch': session['student_branch'],
            'present_days': present_days,
            'working_days': working_days,
            'percentage': percentage,
            'confidence': matched['confidence']
        })
    else:
        return jsonify({'success': False, 'message': message})


# ─── Admin Login ────────────────────────────────────────────────
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.pop('is_student', None)
            session.pop('student_id', None)
            session.pop('student_name', None)
            session.pop('student_reg', None)
            session.pop('student_branch', None)

            session['is_admin'] = True
            session['admin_name'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials!', 'danger')

    return render_template('admin_login.html')


# ─── Admin Dashboard ───────────────────────────────────────────
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('is_admin'):
        flash('Admin access required!', 'danger')
        return redirect(url_for('admin_login'))

    branch_filter = request.args.get('branch', 'all')
    branches = get_all_branches()
    dashboard_data = get_admin_dashboard_data(branch_filter)

    return render_template('admin_dashboard.html',
                           data=dashboard_data,
                           branches=branches,
                           selected_branch=branch_filter,
                           working_days=get_working_days_in_month())


# ─── Admin: Edit Student (UPDATE) ──────────────────────────────
@app.route('/admin/edit/<int:student_id>', methods=['GET', 'POST'])
def admin_edit_student(student_id):
    if not session.get('is_admin'):
        flash('Admin access required!', 'danger')
        return redirect(url_for('admin_login'))

    student = get_student_by_id(student_id)
    if not student:
        flash('Student not found!', 'danger')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        branch = request.form.get('branch', '').strip()

        if not name.replace(' ', '').isalpha():
            flash('Name must contain only alphabets!', 'danger')
            return render_template('admin_edit.html', student=student)

        phone_valid, phone_msg = validate_phone(phone)
        if not phone_valid:
            flash(phone_msg, 'danger')
            return render_template('admin_edit.html', student=student)

        success, message = update_student(student_id, name, phone, branch)
        if success:
            flash(message, 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash(message, 'danger')

    return render_template('admin_edit.html', student=student)


# ─── Admin: Delete Student (DELETE) ────────────────────────────
@app.route('/admin/delete/<int:student_id>', methods=['POST'])
def admin_delete_student(student_id):
    if not session.get('is_admin'):
        flash('Admin access required!', 'danger')
        return redirect(url_for('admin_login'))

    success, message = delete_student(student_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')

    return redirect(url_for('admin_dashboard'))


# ─── Logout ────────────────────────────────────────────────────
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


# ─── Initialize and Run ────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    os.makedirs('face_data', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
