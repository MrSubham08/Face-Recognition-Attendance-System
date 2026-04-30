import os
from flask import Flask, flash, redirect, url_for
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, current_user
from functools import wraps
from .database import get_student_by_id

load_dotenv()
login_manager = LoginManager()
login_manager.login_view = 'auth.student_login'
login_manager.login_message_category = 'warning'

class User(UserMixin):
    def __init__(self, user_id, is_admin=False, **kwargs):
        self.id = user_id
        self.is_admin = is_admin
        for k, v in kwargs.items():
            setattr(self, k, v)
    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    if str(user_id).startswith('admin_'):
        return User(user_id, is_admin=True, name=os.environ.get('ADMIN_USERNAME', 'admin'))
    student = get_student_by_id(int(user_id))
    if student:
        return User(student['id'], is_admin=False, name=student['name'], branch=student['branch'], reg_number=student['reg_number'])
    return None

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            flash('Admin access required!', 'danger')
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def create_app():
    # Point Flask to the templates/static folders in the root directory
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("CRITICAL SECURITY ERROR: No SECRET_KEY set.")
    app.secret_key = SECRET_KEY
    
    login_manager.init_app(app)
    
    from .database import init_db
    init_db()
    os.makedirs('face_data', exist_ok=True)
    
    from .auth.routes import auth_bp
    from .student.routes import student_bp
    from .admin.routes import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    
    # Override Jinja's url_for to resolve Blueprint endpoints without modifying HTML templates
    from flask import url_for as flask_url_for
    def custom_url_for(endpoint, **values):
        if '.' not in endpoint and endpoint != 'static':
            auth_endpoints = ['index', 'register', 'api_validate_reg', 'detect_branch', 'student_login', 'forgot_credentials', 'forgot_verify_face', 'admin_login', 'logout']
            student_endpoints = ['student_dashboard', 'student_history', 'mark_attendance_route']
            admin_endpoints = ['admin_dashboard', 'admin_edit_student', 'admin_delete_student']
            if endpoint in auth_endpoints: endpoint = f"auth.{endpoint}"
            elif endpoint in student_endpoints: endpoint = f"student.{endpoint}"
            elif endpoint in admin_endpoints: endpoint = f"admin.{endpoint}"
        return flask_url_for(endpoint, **values)
        
    app.jinja_env.globals['url_for'] = custom_url_for
    
    return app
