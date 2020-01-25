import os

from flask import Flask, render_template, session, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, \
    current_user, logout_user, login_required
from selectsubjectform import SelectSubjectForm
from db import db, Task, init_database, Subject, add_to_db, User

from config import Config
from create_task_form import CreateTaskform
from login_form import LoginForm
from reg_form import RegForm

SUBJECTS = {1: 'Физика', 2: 'Математика', 3: 'Русский язык', 4: 'История', 5: 'Английский язык'}
SUBJ_TO_PATH = {'Физика': 'phys', 'Математика': 'math', 'Русский язык': 'russian', 'История': 'history',
                'Английский язык': 'english'}

app = Flask(__name__)
app.config.from_object(Config)

db.app = app
db.init_app(app)
init_database()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None:
            flash('User not found', category='danger')
            return redirect(url_for('registration'))
        elif user.check_password(form.password.data) is False:
            flash('Invalid Username or password', category='danger')
            return redirect(url_for('login'))
        else:
            login_user(user)
            flash('Logged in successfully', category='success')
            return redirect(url_for('index'))
    for errors in form.errors.values():
        for error in errors:
            flash(error, category='danger')
    return render_template('loginform.html', form=form, title='Authorization')


@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if current_user.is_authenticated:
        flash('Already logged in', category='danger')
        return redirect(url_for('index'))
    form = RegForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first() is not None:
            flash('Username is busy', category='danger')
            return redirect(url_for('registration'))
        elif User.query.filter_by(email=form.email.data).first() is not None:
            flash('Email is busy', category='danger')
            return redirect(url_for('registration'))
        else:
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            add_to_db([user])
            flash('Successful', category='success')
        return redirect(url_for('login'))
    for errors in form.errors.values():
        for error in errors:
            flash(error, category='danger')
    return render_template('regform.html', form=form, title='Registration')


@app.route('/tasks_generating', methods=['GET', 'POST'])
@login_required
def index():
    form = SelectSubjectForm()
    if form.is_submitted():
        session['subject'] = SUBJ_TO_PATH[SUBJECTS[int(form.select.data)]]
        return redirect(url_for('tasks'))
    return render_template('tasks.html', title='tasks', subjects=SUBJECTS, form=form)


@app.route('/tasks')
def tasks():
    task = Task.query.filter(
        Task.subject_id == Subject.query.filter(Subject.name == session.get('subject')).first().id).all()
    return render_template('oriented_tasks.html', array=task, len=len)


@app.route('/create/task', methods=['GET', 'POST'])
def create_task():
    form = CreateTaskform()
    if form.validate_on_submit():
        subject = Subject.query.filter(Subject.name == SUBJ_TO_PATH[SUBJECTS[int(form.select.data)]]).first()
        task = Task(subject=subject, level=1, title=form.title.data, body=form.body.data, answer=form.answer.data)
        add_to_db([task])
        return redirect(url_for('tasks'))
    return render_template('create_task.html', form=form)
