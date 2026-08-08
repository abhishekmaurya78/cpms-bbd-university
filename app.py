import os
import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import OperationalError
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature, BadSignature, BadData

# Load environment variables
load_dotenv()

# Constant for Super Admin email
SUPERADMIN_EMAIL = os.environ.get('SUPERADMIN_EMAIL', 'abhishekmaurya53957@gmail.com')

# Initialize Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'bbd_university_cpms_secret_key_2026')

# Flask-Mail configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', SUPERADMIN_EMAIL)
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = ('BBD CPMS', app.config['MAIL_USERNAME'])

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Database configuration with PostgreSQL and SQLite fallback
DATABASE_URL = os.environ.get('DATABASE_URL')
POSTGRES_URI = os.environ.get('POSTGRES_URI', 'postgresql://postgres:Abhishek%401234@localhost:5432/cpms_db')
SQLITE_URI = 'sqlite:///cpms.db'

if DATABASE_URL:
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = POSTGRES_URI

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and login manager
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'warning'

# User database model
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    student_profile = db.relationship('StudentProfile', backref='user', uselist=False, cascade="all, delete-orphan")
    company_profile = db.relationship('CompanyProfile', backref='user', uselist=False, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Student profile model
class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    roll_no = db.Column(db.String(50), unique=True, nullable=True)
    branch = db.Column(db.String(100), nullable=True)
    semester = db.Column(db.String(20), nullable=True)
    cgpa = db.Column(db.Float, nullable=True, default=7.0)
    passing_year = db.Column(db.Integer, nullable=True, default=2028)
    resume_link = db.Column(db.String(255), nullable=True, default="https://example.com/resume.pdf")
    skills = db.Column(db.Text, nullable=True)

    applications = db.relationship('Application', backref='student', cascade="all, delete-orphan")

# Company profile model
class CompanyProfile(db.Model):
    __tablename__ = 'company_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    company_name = db.Column(db.String(150), nullable=False)
    industry = db.Column(db.String(100), nullable=False)
    website = db.Column(db.String(150), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)

    jobs = db.relationship('Job', backref='company', cascade="all, delete-orphan")

# Job listing model
class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('company_profiles.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    role_description = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    requirements = db.Column(db.Text, nullable=True)
    eligibility_criteria = db.Column(db.Text, nullable=True)
    min_cgpa = db.Column(db.Float, default=6.0)
    package = db.Column(db.Float, nullable=True)
    salary_package = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    deadline = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='active')
    posted_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    applications = db.relationship('Application', backref='job', cascade="all, delete-orphan")

# Job application model
class Application(db.Model):
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    status = db.Column(db.String(30), default='applied')
    applied_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    applied_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    remarks = db.Column(db.Text, nullable=True)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize database and default super admin account
def init_db():
    with app.app_context():
        try:
            db.create_all()
            with db.engine.connect() as conn:
                for statement in [
                    'ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;',
                    'ALTER TABLE jobs ADD COLUMN IF NOT EXISTS description TEXT;',
                    'ALTER TABLE jobs ADD COLUMN IF NOT EXISTS package DOUBLE PRECISION;',
                    'ALTER TABLE jobs ADD COLUMN IF NOT EXISTS eligibility_criteria TEXT;',
                    'ALTER TABLE jobs ADD COLUMN IF NOT EXISTS posted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP;',
                    'ALTER TABLE student_profiles ADD COLUMN IF NOT EXISTS semester VARCHAR(20);',
                    'ALTER TABLE student_profiles ADD COLUMN IF NOT EXISTS resume_link VARCHAR(255);',
                    'ALTER TABLE applications ADD COLUMN IF NOT EXISTS applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP;'
                ]:
                    try:
                        conn.execute(db.text(statement))
                    except Exception:
                        pass
                conn.commit()
            print(f"Connected to database successfully ({app.config['SQLALCHEMY_DATABASE_URI']}).")
        except Exception as e:
            print(f"Database connection failed ({e}). Falling back to SQLite database...")
            app.config['SQLALCHEMY_DATABASE_URI'] = SQLITE_URI
            db.create_all()
            print(f"Active database: SQLite ({SQLITE_URI})")

        super_admin = User.query.filter_by(email=SUPERADMIN_EMAIL).first()
        if not super_admin:
            super_admin = User(
                email=SUPERADMIN_EMAIL,
                role="superadmin",
                name="Abhishek Maurya (Developer)",
                phone="7800897804",
                is_active=True
            )
            super_admin.set_password("Abhishek@1234")
            db.session.add(super_admin)
            db.session.commit()
            print("Super Admin account ready.")
        else:
            super_admin.role = "superadmin"
            super_admin.name = "Abhishek Maurya (Developer)"
            db.session.commit()
            print("Super Admin account verified and ready.")

# Home page route
@app.route('/')
def index():
    active_jobs_count = Job.query.filter_by(status='active').count()
    placed_students_count = Application.query.filter_by(status='Selected').count()
    total_students = StudentProfile.query.count()
    total_companies = CompanyProfile.query.count()
    return render_template('index.html', 
                           jobs_count=active_jobs_count, 
                           placed_count=placed_students_count,
                           students_count=total_students,
                           companies_count=total_companies)

# Login user controller
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect_by_role(current_user.role)

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect_by_role(user.role)
        else:
            flash('Invalid email address or password. Please try again.', 'danger')

    return render_template('login.html')

# Forgot password
@app.route('/forgot_password', methods=['GET', 'POST'])
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect_by_role(current_user.role)

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if email == 'abhishekmaurya53957@gmail.com':
            flash('Super Admin cannot use forgot password. Please contact developer.', 'danger')
            return redirect(url_for('login'))

        user = User.query.filter_by(email=email).first()

        if user:
            token = serializer.dumps(user.email, salt='password-reset-salt')
            reset_url = url_for('reset_password', token=token, _external=True)

            try:
                msg = Message("Password Reset Request - BBD CPMS", recipients=[user.email])
                msg.body = f"Hello {user.name},\n\nClick the link below to reset your password:\n{reset_url}\n\nIf you did not request this, please ignore."
                mail.send(msg)
                flash('Password reset link has been sent to your email address.', 'success')
            except Exception:
                flash('If an account exists with that email address, a password reset link has been generated.', 'info')
            return redirect(url_for('login'))
        else:
            flash('No account found with that email address. Please verify your email.', 'danger')

    return render_template('forgot_password.html')

# Reset password
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect_by_role(current_user.role)

    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except (SignatureExpired, BadTimeSignature, BadSignature, BadData):
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgot_password'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User account not found.', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not password:
            flash('Password cannot be empty.', 'danger')
        elif confirm_password and password != confirm_password:
            flash('Passwords do not match.', 'danger')
        else:
            user.set_password(password)
            db.session.commit()
            flash('Your password has been updated successfully! Please login.', 'success')
            return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)

# Register user controller
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect_by_role(current_user.role)

    if request.method == 'POST':
        role = request.form.get('role')
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        phone = request.form.get('phone', '').strip()

        if User.query.filter_by(email=email).first():
            flash('Email address is already registered. Please login.', 'warning')
            return redirect(url_for('login'))
        if role == 'superadmin':
            role = 'student'

        new_user = User(email=email, role=role, name=name, phone=phone)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        if role == 'student':
            roll_no = request.form.get('roll_no', f'BBD{new_user.id:04d}')
            branch = request.form.get('branch', 'Computer Science')
            semester = request.form.get('semester', '8th Semester')
            cgpa = float(request.form.get('cgpa', 7.0))
            passing_year = int(request.form.get('passing_year', 2028))
            skills = request.form.get('skills', 'Python, SQL')
            
            student_prof = StudentProfile(
                user_id=new_user.id,
                roll_no=roll_no,
                branch=branch,
                semester=semester,
                cgpa=cgpa,
                passing_year=passing_year,
                skills=skills
            )
            db.session.add(student_prof)

        elif role == 'company':
            company_name = request.form.get('company_name', name)
            industry = request.form.get('industry', 'Technology')
            location = request.form.get('location', 'India')
            website = request.form.get('website', '')
            description = request.form.get('description', '')

            company_prof = CompanyProfile(
                user_id=new_user.id,
                company_name=company_name,
                industry=industry,
                location=location,
                website=website,
                description=description
            )
            db.session.add(company_prof)

        db.session.commit()
        flash('Registration successful! You can now login to your account.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Logout user controller
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

# Helper function to redirect user based on role
def redirect_by_role(role):
    if role == 'superadmin':
        return redirect(url_for('superadmin_dashboard'))
    elif role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'company':
        return redirect(url_for('company_dashboard'))
    elif role == 'student':
        return redirect(url_for('student_dashboard'))
    else:
        return redirect(url_for('index'))

# Super admin dashboard route
@app.route('/superadmin/dashboard')
@login_required
def superadmin_dashboard():
    if current_user.email != 'abhishekmaurya53957@gmail.com':
        flash('Access Denied! You are not authorized to view this page.', 'danger')
        return redirect(url_for('index'))
    total_students = StudentProfile.query.count()
    total_companies = CompanyProfile.query.count()
    total_jobs = Job.query.count()
    
    return render_template('superadmin_dashboard.html', 
                           total_students=total_students,
                           total_companies=total_companies,
                           total_jobs=total_jobs)

# Admin dashboard route
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin' and current_user.email != 'abhishekmaurya53957@gmail.com':
        flash('Unauthorized access.', 'danger')
        return redirect_by_role(current_user.role)

    total_students = StudentProfile.query.count()
    total_companies = CompanyProfile.query.count()
    total_jobs = Job.query.count()
    total_applications = Application.query.count()
    selected_count = Application.query.filter_by(status='Selected').count()
    shortlisted_count = Application.query.filter_by(status='Shortlisted').count()
    applied_count = Application.query.filter_by(status='Applied').count()
    rejected_count = Application.query.filter_by(status='Rejected').count()

    recent_applications = Application.query.order_by(Application.applied_at.desc()).limit(8).all()
    recent_jobs = Job.query.order_by(Job.created_at.desc()).limit(5).all()

    branches = db.session.query(StudentProfile.branch, db.func.count(StudentProfile.id)).group_by(StudentProfile.branch).all()
    branch_labels = [b[0] for b in branches]
    branch_counts = [b[1] for b in branches]

    return render_template('admin_dashboard.html',
                           total_students=total_students,
                           total_companies=total_companies,
                           total_jobs=total_jobs,
                           total_applications=total_applications,
                           selected_count=selected_count,
                           shortlisted_count=shortlisted_count,
                           applied_count=applied_count,
                           rejected_count=rejected_count,
                           recent_applications=recent_applications,
                           recent_jobs=recent_jobs,
                           branch_labels=branch_labels,
                           branch_counts=branch_counts)

# Admin student list route
@app.route('/admin/students')
@login_required
def admin_students():
    if current_user.role != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect_by_role(current_user.role)

    students = StudentProfile.query.join(User).all()
    return render_template('admin_students.html', students=students)

# Admin job list route
@app.route('/admin/jobs')
@login_required
def admin_jobs():
    if current_user.role != 'admin':
        flash('Unauthorized access.', 'danger')
        return redirect_by_role(current_user.role)

    jobs = Job.query.order_by(Job.created_at.desc()).all()
    return render_template('admin_jobs.html', jobs=jobs)

# Admin and company application view route
@app.route('/admin/applications')
@login_required
def admin_applications():
    if current_user.role not in ['admin', 'company']:
        flash('Unauthorized access.', 'danger')
        return redirect_by_role(current_user.role)

    if current_user.role == 'company':
        company_prof = CompanyProfile.query.filter_by(user_id=current_user.id).first()
        job_ids = [j.id for j in Job.query.filter_by(company_id=company_prof.id).all()] if company_prof else []
        applications = Application.query.filter(Application.job_id.in_(job_ids)).order_by(Application.applied_at.desc()).all() if job_ids else []
    else:
        applications = Application.query.order_by(Application.applied_at.desc()).all()

    return render_template('admin_applications.html', applications=applications)

# Application status update controller
@app.route('/application/<int:app_id>/status', methods=['POST'])
@login_required
def update_application_status(app_id):
    if current_user.role not in ['admin', 'company']:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('index'))

    application = Application.query.get_or_404(app_id)
    new_status = request.form.get('status')
    remarks = request.form.get('remarks', '')

    if new_status in ['Applied', 'Shortlisted', 'Rejected', 'Selected']:
        application.status = new_status
        if remarks:
            application.remarks = remarks
        db.session.commit()
        flash(f'Application status updated to "{new_status}".', 'success')
    else:
        flash('Invalid status provided.', 'danger')

    return redirect(request.referrer or url_for('admin_applications'))

# Student dashboard route
@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student' and current_user.email != 'abhishekmaurya53957@gmail.com':
        flash('Unauthorized access.', 'danger')
        return redirect_by_role(current_user.role)

    student_prof = StudentProfile.query.filter_by(user_id=current_user.id).first()
    my_apps = Application.query.filter_by(student_id=student_prof.id).all() if student_prof else []

    applied_jobs_ids = [a.job_id for a in my_apps]
    eligible_jobs = Job.query.filter(Job.min_cgpa <= (student_prof.cgpa if student_prof else 0), Job.status == 'active').all()

    selected_count = sum(1 for a in my_apps if a.status == 'Selected')
    shortlisted_count = sum(1 for a in my_apps if a.status == 'Shortlisted')

    return render_template('student_dashboard.html',
                           student=student_prof,
                           applications=my_apps,
                           applied_jobs_ids=applied_jobs_ids,
                           eligible_jobs=eligible_jobs,
                           selected_count=selected_count,
                           shortlisted_count=shortlisted_count)

# Browse jobs route
@app.route('/jobs')
@login_required
def jobs():
    search_query = request.args.get('search', '').strip()
    branch_filter = request.args.get('branch', '').strip()

    query = Job.query.filter_by(status='active')
    if search_query:
        query = query.filter(Job.title.ilike(f'%{search_query}%') | Job.location.ilike(f'%{search_query}%'))

    all_jobs = query.order_by(Job.created_at.desc()).all()

    applied_job_ids = []
    student_prof = None
    if current_user.role == 'student':
        student_prof = StudentProfile.query.filter_by(user_id=current_user.id).first()
        if student_prof:
            applied_job_ids = [a.job_id for a in Application.query.filter_by(student_id=student_prof.id).all()]

    return render_template('jobs.html', jobs=all_jobs, applied_job_ids=applied_job_ids, student=student_prof)

# Apply job controller
@app.route('/apply/<int:job_id>', methods=['POST'])
@login_required
def apply_job(job_id):
    if current_user.role != 'student':
        flash('Only students can apply for jobs.', 'danger')
        return redirect(url_for('jobs'))

    student_prof = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if not student_prof:
        flash('Please complete your student profile before applying.', 'warning')
        return redirect(url_for('student_dashboard'))

    job = Job.query.get_or_404(job_id)

    if student_prof.cgpa < job.min_cgpa:
        flash(f'Your CGPA ({student_prof.cgpa}) does not meet the minimum required CGPA ({job.min_cgpa}) for this job.', 'danger')
        return redirect(url_for('jobs'))

    existing_app = Application.query.filter_by(job_id=job.id, student_id=student_prof.id).first()
    if existing_app:
        flash('You have already applied for this job opportunity.', 'info')
        return redirect(url_for('my_applications'))

    new_app = Application(
        job_id=job.id,
        student_id=student_prof.id,
        status='Applied',
        remarks='Application submitted via CPMS Portal'
    )
    db.session.add(new_app)
    db.session.commit()

    flash(f'Successfully applied for "{job.title}" at {job.company.company_name}!', 'success')
    return redirect(url_for('my_applications'))

# My applications route
@app.route('/my-applications')
@login_required
def my_applications():
    if current_user.role != 'student':
        flash('Unauthorized access.', 'danger')
        return redirect_by_role(current_user.role)

    student_prof = StudentProfile.query.filter_by(user_id=current_user.id).first()
    applications = Application.query.filter_by(student_id=student_prof.id).order_by(Application.applied_at.desc()).all() if student_prof else []

    return render_template('my_applications.html', applications=applications, student=student_prof)

# Company dashboard route
@app.route('/company/dashboard')
@login_required
def company_dashboard():
    if current_user.role != 'company' and current_user.email != 'abhishekmaurya53957@gmail.com':
        flash('Unauthorized access.', 'danger')
        return redirect_by_role(current_user.role)

    company_prof = CompanyProfile.query.filter_by(user_id=current_user.id).first()
    posted_jobs = Job.query.filter_by(company_id=company_prof.id).order_by(Job.created_at.desc()).all() if company_prof else []
    
    total_posted_jobs = len(posted_jobs)
    job_ids = [j.id for j in posted_jobs]
    total_applicants = Application.query.filter(Application.job_id.in_(job_ids)).count() if job_ids else 0
    shortlisted_count = Application.query.filter(Application.job_id.in_(job_ids), Application.status == 'Shortlisted').count() if job_ids else 0
    selected_count = Application.query.filter(Application.job_id.in_(job_ids), Application.status == 'Selected').count() if job_ids else 0

    return render_template('company_dashboard.html',
                           company=company_prof,
                           jobs=posted_jobs,
                           total_posted_jobs=total_posted_jobs,
                           total_applicants=total_applicants,
                           shortlisted_count=shortlisted_count,
                           selected_count=selected_count)

# Post job controller
@app.route('/post-job', methods=['GET', 'POST'])
@login_required
def post_job():
    if current_user.role not in ['company', 'admin']:
        flash('Only verified recruiters and admins can post job listings.', 'danger')
        return redirect_by_role(current_user.role)

    company_prof = CompanyProfile.query.filter_by(user_id=current_user.id).first()
    if not company_prof and current_user.role == 'company':
        flash('Please complete your company profile details.', 'warning')
        return redirect(url_for('company_dashboard'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        role_description = request.form.get('role_description', '').strip()
        requirements = request.form.get('requirements', '').strip()
        min_cgpa = float(request.form.get('min_cgpa', 6.0))
        salary_package = request.form.get('salary_package', '').strip()
        location = request.form.get('location', '').strip()
        deadline = request.form.get('deadline', '').strip()

        company_id = company_prof.id if company_prof else CompanyProfile.query.first().id

        new_job = Job(
            company_id=company_id,
            title=title,
            role_description=role_description,
            requirements=requirements,
            min_cgpa=min_cgpa,
            salary_package=salary_package,
            location=location,
            deadline=deadline,
            status='active'
        )
        db.session.add(new_job)
        db.session.commit()

        flash(f'Job posting "{title}" published successfully!', 'success')
        return redirect(url_for('company_dashboard') if current_user.role == 'company' else url_for('admin_jobs'))

    return render_template('post_job.html', company=company_prof)

# Toggle job status controller
@app.route('/job/<int:job_id>/toggle-status', methods=['POST'])
@login_required
def toggle_job_status(job_id):
    job = Job.query.get_or_404(job_id)
    job.status = 'closed' if job.status == 'active' else 'active'
    db.session.commit()
    flash(f'Job status changed to {job.status.upper()}.', 'info')
    return redirect(request.referrer or url_for('company_dashboard'))

# Role redirect helper route
@app.route('/redirect_by_role/<role>')
def redirect_by_role_route(role):
    return redirect_by_role(role)

# Page not found error handler
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

# Internal server error handler
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Main entry point
if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)