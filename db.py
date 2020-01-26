import os
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy

SUBJECTS = ['phys', 'math', 'history', 'russian', 'english']
PERMISSIONS = ['admin', 'student']

db = SQLAlchemy()

users_subjects_like = db.Table('UserTagsLike', db.metadata, db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                               db.Column('subject_id', db.Integer, db.ForeignKey('subject.id')))
users_subjects_dislike = db.Table('UserTagsDislike', db.metadata,
                                  db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                                  db.Column('subject_id', db.Integer, db.ForeignKey('subject.id')))
users_tasks = db.Table('UsersTasks', db.metadata,
                       db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                       db.Column('task_id', db.Integer, db.ForeignKey('task.id')))


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    subject = db.relationship('Subject', backref=db.backref('tasks', lazy='dynamic'))
    level = db.Column(db.Integer)
    day_task = db.Column(db.Boolean)
    is_checked = db.Column(db.Boolean)
    title = db.Column(db.String(140), unique=True)
    body = db.Column(db.Text)
    answer = db.Column(db.String(100))


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', backref=db.backref('messages', lazy='dynamic'))
    msg = db.Column(db.Text, nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('task.id'))
    topic = db.relationship('Task', backref=db.backref('messages', lazy='dynamic'))


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), unique=True)


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), index=True, nullable=False, unique=True)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(128), index=True, nullable=False, unique=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', backref=db.backref('users'))
    solved_tasks = db.relationship('Task', secondary=users_tasks, backref=db.backref('users', lazy='dynamic'))
    experience = db.Column(db.Integer, default=0)
    last_date = db.Column(db.DateTime, default=datetime.now())
    boost = db.Column(db.Integer, default=7)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {} {}>'.format(self.username, self.email)

    subjects_like = db.relationship('Subject', secondary=users_subjects_like,
                                    backref=db.backref('user_like', lazy='dynamic'), lazy='dynamic')
    subjects_dislike = db.relationship('Subject', secondary=users_subjects_like,
                                       backref=db.backref('user_dislike', lazy='dynamic'), lazy='dynamic')


def add_to_db(array):
    db.session.add_all(array)
    db.session.commit()


def init_base_subjects():
    db.session.add_all([Subject(name=el) for el in SUBJECTS])
    db.session.commit()


def init_permission():
    db.session.add_all([Role(name=el) for el in PERMISSIONS])
    db.session.commit()


def init_database():
    if 'test.db' not in os.listdir('.'):
        db.create_all()
        init_base_subjects()
        init_permission()
        admin = User(username='root', email='root@root.ru')
        admin.set_password('admin')
        role = Role.query.filter_by(name='admin').first()
        role.users.append(admin)
        add_to_db([admin, role])
