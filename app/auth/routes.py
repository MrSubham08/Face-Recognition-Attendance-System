from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from flask_login import login_user, logout_user
from ..database import (
    add_student, get_student_by_reg, get_student_by_id,
    get_branch_from_reg, normalize_dob, BRANCH_CODES,
    validate_reg_number, validate_dob_age, validate_phone
)
from ..face_utils import encode_face_from_base64, match_face
from ..__init__ import User
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    return render_template('index.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        if not all([data.get(k) for k in ('name', 'reg_number', 'dob', 'phone', 'branch', 'face_image')]):
            return jsonify({'success': False, 'message': 'All fields required!'})
        
        is_valid, msg, branch = validate_reg_number(data['reg_number'])
        if not is_valid: return jsonify({'success': False, 'message': msg})
        
        existing = get_student_by_reg(data['reg_number'])
        if existing: return jsonify({'success': False, 'message': 'Already registered.', 'already_registered': True})
        
        encoding, msg = encode_face_from_base64(data['face_image'])
        if encoding is None: return jsonify({'success': False, 'message': msg})
        
        success, message = add_student(data['name'], data['reg_number'], data['dob'], data['phone'], data['branch'], encoding)
        return jsonify({'success': success, 'message': message})
    return render_template('register.html', branch_codes=BRANCH_CODES)

@auth_bp.route('/api/validate_reg', methods=['POST'])
def api_validate_reg():
    data = request.get_json()
    reg_number = data.get('reg_number', '').strip()
    if not reg_number: return jsonify({'valid': False, 'message': ''})
    if not reg_number.isdigit(): return jsonify({'valid': False, 'message': 'Only numeric digits allowed.'})
    if len(reg_number) < 11: return jsonify({'valid': False, 'message': f'Keep typing... ({len(reg_number)}/11 digits)'})
    if len(reg_number) > 11: return jsonify({'valid': False, 'message': f'Too many digits!'})
    is_valid, msg, branch = validate_reg_number(reg_number)
    return jsonify({'valid': is_valid, 'message': msg, 'branch': branch if is_valid else None})

@auth_bp.route('/api/detect_branch', methods=['POST'])
def detect_branch():
    branch = get_branch_from_reg(request.get_json().get('reg_number', ''))
    return jsonify({'success': bool(branch), 'branch': branch})

@auth_bp.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        student = get_student_by_reg(request.form.get('reg_number', '').strip())
        if student and student['dob'] == normalize_dob(request.form.get('dob', '').strip()):
            user = User(student['id'], is_admin=False, name=student['name'], branch=student['branch'], reg_number=student['reg_number'])
            login_user(user)
            return redirect(url_for('student.student_dashboard'))
        flash('Invalid Registration Number or Date of Birth!', 'danger')
    return render_template('student_login.html')

@auth_bp.route('/student/forgot', methods=['GET'])
def forgot_credentials(): return render_template('forgot_credentials.html')

@auth_bp.route('/student/forgot/verify', methods=['POST'])
def forgot_verify_face():
    data = request.get_json()
    matched, msg = match_face(data.get('face_image', ''))
    if matched is None: return jsonify({'success': False, 'message': msg})
    student = get_student_by_id(matched['id'])
    if not student: return jsonify({'success': False, 'message': 'Student not found.'})
    dob = student['dob']
    return jsonify({
        'success': True, 'message': f'Face matched with {matched["confidence"]}% confidence!',
        'name': student['name'], 'reg_number': student['reg_number'], 'branch': student['branch'],
        'dob_display': f"{dob[:4]}-**-{dob[8:]}", 'dob_full': dob, 'confidence': matched['confidence']
    })

@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        if username == os.environ.get('ADMIN_USERNAME', 'admin') and \
           request.form.get('password') == os.environ.get('ADMIN_PASSWORD'):
            user = User(f"admin_{username}", is_admin=True)
            login_user(user)
            return redirect(url_for('admin.admin_dashboard'))
        flash('Invalid admin credentials!', 'danger')
    return render_template('admin_login.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('auth.index'))
