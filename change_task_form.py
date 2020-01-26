from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField

SUBJECTS = {1: 'Физика', 2: 'Математика', 3: 'Русский язык', 4: 'История', 5: 'Английский'}


class ChangeTaskForm(FlaskForm):
    select = SelectField(choices=[el for el in SUBJECTS.items()])
    title = StringField('Title')
    body = TextAreaField('Body')
    answer = StringField('Answer')
    level = SelectField(choices=[(el, el) for el in range(1, 11)])
    submit = SubmitField('Одобрить!')
