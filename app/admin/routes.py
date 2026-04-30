from flask import Blueprint, render_template, request, flash, redirect, url_for
from ..__init__ import admin_required
from ..database import get_all_branches, get_admin_dashboard_data, get_working_days_in_month, get_student_by_id, update_student, delete_student, validate_phone

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@admin_required
def admin_dashboard():
    branch_filter = request.args.get('branch', 'all')
    return render_template('admin_dashboard.html',
                           data=get_admin_dashboard_data(branch_filter),
                           branches=get_all_branches(),
                           selected_branch=branch_filter,
                           working_days=get_working_days_in_month())

@admin_bp.route('/edit/<int:student_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_student(student_id):
    student = get_student_by_id(student_id)
    if not student:
        flash('Student not found!', 'danger')
        return redirect(url_for('admin.admin_dashboard'))

    if request.method == 'POST':
        success, message = update_student(student_id, request.form.get('name'), request.form.get('phone'), request.form.get('branch'))
        flash(message, 'success' if success else 'danger')
        if success: return redirect(url_for('admin.admin_dashboard'))

    return render_template('admin_edit.html', student=student)

@admin_bp.route('/delete/<int:student_id>', methods=['POST'])
@admin_required
def admin_delete_student(student_id):
    success, message = delete_student(student_id)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('admin.admin_dashboard'))
