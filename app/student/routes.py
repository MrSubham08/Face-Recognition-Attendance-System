from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from ..database import check_attendance_today, get_attendance_count, get_working_days_in_month, get_attendance_percentage, get_attendance_history, mark_attendance
from ..face_utils import match_face

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@login_required
def student_dashboard():
    return render_template('student_dashboard.html',
                           already_marked=check_attendance_today(current_user.id),
                           present_days=get_attendance_count(current_user.id),
                           working_days=get_working_days_in_month(),
                           percentage=get_attendance_percentage(current_user.id))

@student_bp.route('/history')
@login_required
def student_history():
    return render_template('student_history.html',
                           history=get_attendance_history(current_user.id),
                           present_days=get_attendance_count(current_user.id),
                           working_days=get_working_days_in_month(),
                           percentage=get_attendance_percentage(current_user.id))

@student_bp.route('/mark_attendance', methods=['POST'])
@login_required
def mark_attendance_route():
    matched, msg = match_face(request.get_json().get('face_image', ''))
    if matched is None: return jsonify({'success': False, 'message': msg})
    if matched['id'] != current_user.id: return jsonify({'success': False, 'message': 'Face does not match!'})
    
    success, message = mark_attendance(current_user.id)
    if success:
        return jsonify({
            'success': True, 'message': message, 'student_name': current_user.name,
            'branch': getattr(current_user, 'branch', ''),
            'present_days': get_attendance_count(current_user.id),
            'working_days': get_working_days_in_month(),
            'percentage': get_attendance_percentage(current_user.id),
            'confidence': matched['confidence']
        })
    return jsonify({'success': False, 'message': message})
