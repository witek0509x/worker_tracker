from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///worker_tracking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_worker = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to Worker (one-to-one)
    worker = db.relationship('Worker', backref='user', uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Worker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Worker {self.name}>'

class ServiceJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(200), nullable=False)
    worker_id = db.Column(db.Integer, db.ForeignKey('worker.id'), nullable=False)
    status = db.Column(db.String(20), default='assigned')  # assigned, arrived, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    arrived_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    worker = db.relationship('Worker', backref=db.backref('jobs', lazy=True))
    
    def __repr__(self):
        return f'<ServiceJob {self.title}>'

class StatusLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('service_job.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # arrived, completed
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
    job = db.relationship('ServiceJob', backref=db.backref('logs', lazy=True))
    
    def __repr__(self):
        return f'<StatusLog {self.status} for Job {self.job_id}>'

# Routes
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirect based on role if already logged in
        if current_user.is_admin:
            return redirect(url_for('index'))
        elif current_user.is_worker and current_user.worker:
            return redirect(url_for('worker_dashboard', worker_id=current_user.worker.id))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Zalogowano pomyślnie.', 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            if user.is_admin:
                return redirect(url_for('index'))
            else:
                return redirect(url_for('worker_dashboard', worker_id=user.worker.id))
        else:
            flash('Nieprawidłowa nazwa użytkownika lub hasło.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Wylogowano pomyślnie.', 'success')
    return redirect(url_for('login'))

# Updated index route to handle role-based redirection
@app.route('/')
@app.route('/dashboard')
@login_required
def index():
    # Admin dashboard
    if current_user.is_admin:
        jobs = ServiceJob.query.order_by(ServiceJob.created_at.desc()).all()
        return render_template('index.html', jobs=jobs)
    # Worker dashboard
    elif current_user.is_worker and current_user.worker:
        return redirect(url_for('worker_dashboard', worker_id=current_user.worker.id))
    else:
        flash('Nieautoryzowany dostęp.', 'error')
        return redirect(url_for('login'))

# Protect admin-only routes
@app.route('/workers')
@login_required
def workers():
    if not current_user.is_admin:
        flash('Dostęp zabroniony.', 'error')
        return redirect(url_for('index'))
    workers = Worker.query.all()
    return render_template('workers.html', workers=workers)

@app.route('/add_worker', methods=['GET', 'POST'])
@login_required
def add_worker():
    if not current_user.is_admin:
        flash('Dostęp zabroniony.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form.get('phone', '')
        username = request.form['username']
        password = request.form['password']

        # Check duplicates
        if User.query.filter_by(username=username).first():
            flash('Nazwa użytkownika już istnieje.', 'error')
            return redirect(url_for('add_worker'))
        if User.query.filter_by(email=email).first():
            flash('Adres e-mail już istnieje.', 'error')
            return redirect(url_for('add_worker'))

        # Create user account for worker
        user = User(username=username, email=email, is_worker=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Create worker profile
        worker = Worker(name=name, email=email, phone=phone, user_id=user.id)
        db.session.add(worker)
        db.session.commit()

        flash(f'Pracownik dodany! Tymczasowe hasło: {password}', 'success')
        return redirect(url_for('workers'))

    return render_template('add_worker.html')

# Protect add_job route for admin only
@app.route('/add_job', methods=['GET', 'POST'])
@login_required
def add_job():
    if not current_user.is_admin:
        flash('Dostęp zabroniony.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description', '')
        location = request.form['location']
        worker_id = request.form['worker_id']
        
        job = ServiceJob(title=title, description=description, location=location, worker_id=worker_id)
        db.session.add(job)
        db.session.commit()
        
        flash('Zlecenie utworzono pomyślnie!', 'success')
        return redirect(url_for('index'))
    
    workers = Worker.query.all()
    return render_template('add_job.html', workers=workers)

# Worker Dashboard restricted
@app.route('/worker_dashboard/<int:worker_id>')
@login_required
def worker_dashboard(worker_id):
    if current_user.is_worker:
        if current_user.worker and current_user.worker.id != worker_id:
            flash('Dostęp zabroniony.', 'error')
            return redirect(url_for('index'))
    elif not current_user.is_admin:
        flash('Dostęp zabroniony.', 'error')
        return redirect(url_for('index'))

    worker = Worker.query.get_or_404(worker_id)
    jobs = ServiceJob.query.filter_by(worker_id=worker_id).order_by(ServiceJob.created_at.desc()).all()
    return render_template('worker_dashboard.html', worker=worker, jobs=jobs)

# Arrival and completion routes require authorization
@app.route('/log_arrival/<int:job_id>', methods=['POST'])
@login_required
def log_arrival(job_id):
    job = ServiceJob.query.get_or_404(job_id)
    # Check permission
    if current_user.is_worker and (not current_user.worker or job.worker_id != current_user.worker.id):
        flash('Dostęp zabroniony.', 'error')
        return redirect(url_for('index'))
    
    notes = request.form.get('notes', '')
    if job.status == 'assigned':
        job.status = 'arrived'
        job.arrived_at = datetime.utcnow()
        log = StatusLog(job_id=job_id, status='arrived', notes=notes,
                        latitude=request.form.get('lat', type=float),
                        longitude=request.form.get('lon', type=float))
        db.session.add(log)
        db.session.commit()
        flash('Przyjazd został zapisany.', 'success')
    else:
        flash('Status zlecenia nie pozwala na oznaczenie przyjazdu.', 'error')
    return redirect(url_for('job_detail', job_id=job_id))

@app.route('/log_completion/<int:job_id>', methods=['POST'])
@login_required
def log_completion(job_id):
    job = ServiceJob.query.get_or_404(job_id)
    # Check permission
    if current_user.is_worker and (not current_user.worker or job.worker_id != current_user.worker.id):
        flash('Dostęp zabroniony.', 'error')
        return redirect(url_for('index'))

    notes = request.form.get('notes', '')
    if job.status == 'arrived':
        job.status = 'completed'
        job.completed_at = datetime.utcnow()
        log = StatusLog(job_id=job_id, status='completed', notes=notes,
                        latitude=request.form.get('lat', type=float),
                        longitude=request.form.get('lon', type=float))
        db.session.add(log)
        db.session.commit()
        flash('Zlecenie zakończone pomyślnie!', 'success')
    else:
        flash('Aby zakończyć, status musi być "W trakcie".', 'error')
    return redirect(url_for('job_detail', job_id=job_id))

# API endpoints for mobile/simple interface
@app.route('/api/jobs/<int:worker_id>')
def api_worker_jobs(worker_id):
    jobs = ServiceJob.query.filter_by(worker_id=worker_id).all()
    return jsonify([{
        'id': job.id,
        'title': job.title,
        'location': job.location,
        'status': job.status,
        'created_at': job.created_at.isoformat()
    } for job in jobs])

@app.route('/api/log_status/<int:job_id>', methods=['POST'])
def api_log_status(job_id):
    job = ServiceJob.query.get_or_404(job_id)
    data = request.get_json()
    status = data.get('status')
    notes = data.get('notes', '')
    
    if status == 'arrived' and job.status == 'assigned':
        job.status = 'arrived'
        job.arrived_at = datetime.utcnow()
        lat = data.get('lat')
        lon = data.get('lon')
        log = StatusLog(job_id=job_id, status='arrived', notes=notes, latitude=lat, longitude=lon)
        db.session.add(log)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Arrival logged'})
    
    elif status == 'completed' and job.status == 'arrived':
        job.status = 'completed'
        job.completed_at = datetime.utcnow()
        lat = data.get('lat')
        lon = data.get('lon')
        log = StatusLog(job_id=job_id, status='completed', notes=notes, latitude=lat, longitude=lon)
        db.session.add(log)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Completion logged'})
    
    return jsonify({'success': False, 'message': 'Invalid status transition'})

# Job detail route with access control
@app.route('/job/<int:job_id>')
@login_required
def job_detail(job_id):
    job = ServiceJob.query.get_or_404(job_id)
    # Permissions: worker assigned to job or admin
    if current_user.is_worker and (not current_user.worker or job.worker_id != current_user.worker.id):
        flash('Dostęp zabroniony.', 'error')
        return redirect(url_for('index'))
    logs = StatusLog.query.filter_by(job_id=job_id).order_by(StatusLog.timestamp.desc()).all()
    return render_template('job_detail.html', job=job, logs=logs)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create default admin user if none exists
        if not User.query.filter_by(is_admin=True).first():
            admin = User(username='admin', email='admin@example.com', is_admin=True)
            admin.set_password('adminpass')
            db.session.add(admin)
            db.session.commit()
            print('Created default admin user: admin / adminpass')
    app.run(debug=True, host='0.0.0.0', port=5000) 