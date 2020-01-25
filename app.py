import os
from datetime import datetime

from flask import Flask, render_template, session, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, \
    current_user, logout_user, login_required
from apscheduler.schedulers.background import BackgroundScheduler
from selectsubjectform import SelectSubjectForm
from db import db, Task, init_database, Subject, add_to_db, User

from config import Config
from create_task_form import CreateTaskform
from login_form import LoginForm
from reg_form import RegForm
from SolverForm import SolverForm

SUBJECTS = {1: 'Физика', 2: 'Математика', 3: 'Русский язык', 4: 'История', 5: 'Английский язык'}
SUBJ_TO_PATH = {'Физика': 'phys', 'Математика': 'math', 'Русский язык': 'russian', 'История': 'history',
                'Английский язык': 'english'}
JOB_TO_ROLE = {'1': 'student', '2': 'teacher'}

app = Flask(__name__)
app.config.from_object(Config)

db.app = app
db.init_app(app)
init_database()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

scheduler = BackgroundScheduler()
scheduler.start()


def generate_day_task():
    if len(Task.query.all()) > 0:
        task = sorted(Task.query.all(), key=lambda x: len(x.users.all()))
        if len(Task.query.filter(Task.day_task == True).all()) == 0:
            task[0].day_task = True
            add_to_db([task[0]])
        else:
            task1 = Task.query.filter(Task.day_task == True).first()
            task1.day_task = False
            task[0].day_task = True
            add_to_db([task[0], task1])


scheduler.add_job(func=generate_day_task, trigger="interval", seconds=86400)


def check_time():
    if 86400 < (datetime.now() - current_user.last_date).total_seconds() < 86400 * 2:
        current_user.boost = 10
        add_to_db([current_user])


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
            return redirect(url_for('tasks_gen'))
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


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/d')
def t():
    generate_day_task()
    return 'ok'


@app.route('/day_task')
@login_required
def task_of_day():
    task = Task.query.filter(Task.day_task == True).first()
    if task is None:
        return render_template('fail.html')
    return redirect('/tasks/{}'.format(task.id))


@app.route('/tasks/<int:task_id>', methods=['GET', 'POST'])
@login_required
def solve_task(task_id):
    task = Task.query.filter_by(id=task_id).first()
    form = SolverForm()
    if form.validate_on_submit():
        if form.answer.data == task.answer:
            check_time()
            if task.day_task:
                current_user.experience += task.level * current_user.boost * 3 * task.level
            else:
                current_user.experience += task.level * current_user.boost
            flash('Теперь ваш опыт составляет {} очков!'.format(current_user.experience), category='success')
            flash('Верно! Ваш опыт повышается!', category='success')
            current_user.solved_tasks.append(task)
            current_user.boost = 7
            current_user.last_date = datetime.now()
            add_to_db([current_user])
            return redirect(url_for('tasks'))
        else:
            flash('Неверный ответ :с Попробуй ещё раз', category='danger')
            return redirect('/tasks/{}'.format(task_id))
    return render_template('solve_task.html', task=task, form=form)


@app.route('/rating')
def rating():
    users = User.query.all()
    users.sort(key=lambda x: x.experience, reverse=True)
    return render_template('rating.html', array=enumerate(users, start=1))


@app.route('/tasks/generating', methods=['GET', 'POST'])
@login_required
def tasks_gen():
    form = SelectSubjectForm()
    if form.is_submitted():
        session['subject'] = SUBJ_TO_PATH[SUBJECTS[int(form.select.data)]]
        return redirect(url_for('tasks'))
    return render_template('tasks.html', title='tasks', subjects=SUBJECTS, form=form)


@app.route('/tasks')
@login_required
def tasks():
    task = Task.query.filter(
        Task.subject_id == Subject.query.filter(Subject.name == session.get('subject')).first().id).all()
    task = [el for el in task if el not in current_user.solved_tasks and el.level >= (current_user.experience // 2)]
    return render_template('oriented_tasks.html', array=task, len=len)


@app.route('/tasks/create', methods=['GET', 'POST'])
@login_required
def create_task():
    form = CreateTaskform()
    if form.is_submitted():
        subject = Subject.query.filter(Subject.name == SUBJ_TO_PATH[SUBJECTS[int(form.select.data)]]).first()
        task = Task(subject=subject, level=form.level.data, title=form.title.data, body=form.body.data,
                    answer=form.answer.data)
        add_to_db([task])
        return redirect(url_for('tasks_gen'))
    return render_template('create_task.html', form=form)
