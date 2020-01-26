import os
from datetime import datetime

from flask import Flask, render_template, session, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, \
    current_user, logout_user, login_required
from numpy import mean
from apscheduler.schedulers.background import BackgroundScheduler
from selectsubjectform import SelectSubjectForm
from db import db, Task, init_database, Subject, add_to_db, User, Message

from config import Config
from create_task_form import CreateTaskform
from login_form import LoginForm
from reg_form import RegForm
from SolverForm import SolverForm
from change_task_form import ChangeTaskForm
from comment_form import CommentForm

SUBJECTS = {1: 'Физика', 2: 'Математика', 3: 'Русский язык', 4: 'История', 5: 'Английский язык'}
SUBJECTS_ENG_TO_ID = {'phys': 1, 'math': 2, 'russian': 3, 'history': 4 , 'english': 5}
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

scheduler = BackgroundScheduler()
scheduler.start()


def generate_day_task():
    if len(Task.query.all()) > 0:
        task = sorted(Task.query.all(), key=lambda x: len(x.users.all()))
        users_mean_level = mean([u.experience for u in User.query.all()])
        if len(Task.query.filter(Task.day_task == True).all()) == 0:
            if (task[0].level)**2 >= users_mean_level / 7:
                task[0].day_task = True
                add_to_db([task[0]])
            else:
                hard_task = max(task, key=lambda x: x.level)
                hard_task.day_task = True
                add_to_db([hard_task])
        else:
            task1 = Task.query.filter(Task.day_task == True).first()
            task1.day_task = False
            if task[0].level**2 >= users_mean_level / 7:
                task[0].day_task = True
                add_to_db([task[0]])
            else:
                hard_task = max(task, key=lambda x: x.level)
                hard_task.day_task = True
                add_to_db([hard_task])
            add_to_db([task1])


scheduler.add_job(func=generate_day_task, trigger="interval", seconds=86400)


def check_time():
    if 3600*8 < (datetime.now() - current_user.last_date).total_seconds() < 3600*24:
        flash('У вас появился бонус: ваш множитель баллов за решение задачи возрастает!')
        current_user.boost = 10
        current_user.last_date = datetime.now()
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
            flash('Invalid Username or password', category='danger')
            return redirect(url_for('login'))
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


@app.route('/tasks/check')
@login_required
def check_tasks():
    if current_user.role_id == 1:
        task = Task.query.filter_by(is_checked=False).all()
        if len(task) == 0:
            flash('Нет задач для проверки', category='success')
            return redirect('/')
        return render_template('check_task.html', array=enumerate(task, start=1))
    flash('Вам сюда нельзя >:(', category='danger')
    return redirect('/')


@app.route('/tasks/confirm/<int:task_id>')
@login_required
def confirm_task(task_id):
    if current_user.role_id == 1:
        task = Task.query.filter_by(id=task_id).first()
        task.is_checked = True
        add_to_db([task])
        return redirect(url_for('check_tasks'))
    flash('You dont have enough rights for this action', category='danger')
    return redirect('/')


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
    return redirect(url_for('all_tasks'))


@app.route('/day_task')
@login_required
def task_of_day():
    task = Task.query.filter(Task.day_task == True).first()
    if task is None:
        return render_template('fail.html')
    if task in current_user.solved_tasks:
        flash('Извините, но Вы уже решили эту задачку', category='danger')
        return redirect('/')
    return redirect('/tasks/{}'.format(task.id))


@app.route('/tasks')
@login_required
def all_tasks():
    task = Task.query.filter_by(is_checked=True)
    return render_template('all_tasks.html', array=enumerate(task, start=1))


@app.route('/tasks/<int:task_id>', methods=['GET', 'POST'])
@login_required
def solve_task(task_id):
    task = Task.query.filter_by(id=task_id, is_checked=True).first()
    form = SolverForm()
    form2 = CommentForm()
    check_time()
    if form.validate_on_submit():
        if form.answer.data == task.answer:
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
            return redirect('/rating')
        else:
            flash('Неверный ответ :с Попробуй ещё раз', category='danger')
            return redirect('/tasks/{}'.format(task_id))
    elif form2.validate_on_submit():
        msg = Message(msg=form2.comment.data)
        task.messages.append(msg)
        current_user.messages.append(msg)
        add_to_db([msg, task, current_user])
        form2.comment.data = ''
        return render_template('solve_task.html', task=task, form=form, form2=form2, messages=task.messages)
    return render_template('solve_task.html', task=task, form=form, form2=form2, messages=task.messages)


@app.route('/rating')
@login_required
def rating():
    users = User.query.all()
    users.sort(key=lambda x: x.experience, reverse=True)
    return render_template('rating.html', array=enumerate(users, start=1))


@app.route('/progress')
@login_required
def progress():
    return render_template('progress.html')


@app.route('/tasks/change/<int:task_id>', methods=['GET', 'POST'])
@login_required
def change(task_id):
    task = Task.query.filter_by(id=task_id).first()
    form = ChangeTaskForm()
    form.title.data = task.title
    form.body.data = task.body
    form.answer.data = task.answer
    form.select.data = SUBJECTS_ENG_TO_ID[task.subject.name]
    if form.is_submitted():
        subject = Subject.query.filter(Subject.name == SUBJ_TO_PATH[SUBJECTS[int(form.select.data)]]).first()
        if task.id == Task.query.filter_by(title=form.title.data).first().id:
            task.title = form.title.data
            task.body = form.body.data
            task.level = form.level.data
            task.answer = form.answer.data
            task.subject = subject
            task.is_checked = True
            add_to_db([subject, task])
            flash('Задача успешно добавлена', category='success')
            return redirect(url_for('check_tasks'))
        flash('Задача с таким названием уже существует', category='danger')
        return redirect('/tasks/change/{}'.format(task_id))
    return render_template('change_task.html', form=form)


@app.route('/tasks/generating', methods=['GET', 'POST'])
@login_required
def tasks_gen():
    form = SelectSubjectForm()
    if form.is_submitted():
        return redirect('/tasks/{}'.format(SUBJ_TO_PATH[SUBJECTS[int(form.select.data)]]))
    return render_template('tasks.html', title='tasks', subjects=SUBJECTS, form=form)


@app.route('/tasks/<string:subj>')
@login_required
def tasks(subj):
    task = Task.query.filter(
        Task.subject_id == Subject.query.filter(Subject.name == subj).first().id).all()
    task = [el for el in task if el not in current_user.solved_tasks and el.level >= (current_user.experience // 2) and el.is_checked]
    return render_template('oriented_tasks.html', array=task, len=len)


@app.route('/tasks/create', methods=['GET', 'POST'])
@login_required
def create_task():
    form = CreateTaskform()
    if form.is_submitted():
        subject = Subject.query.filter(Subject.name == SUBJ_TO_PATH[SUBJECTS[int(form.select.data)]]).first()
        if Task.query.filter_by(title=form.title.data).first() is None:
            task = Task(subject=subject, level=form.level.data, title=form.title.data, body=form.body.data,
                        answer=form.answer.data, is_checked=False)
            add_to_db([task])
            flash('Задача успешно отправлена на модерацию!', category='success')
            return redirect(url_for('all_tasks'))
        flash('Задача с таким названием уже существует', category='danger')
        return redirect('/tasks/create')
    return render_template('create_task.html', form=form)
