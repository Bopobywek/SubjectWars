from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, InputRequired

SUBJECTS = {1: 'Физика', 2: 'Математика', 3: 'Русский язык', 4: 'История', 5: 'Английский'}


class SelectSubjectForm(FlaskForm):
    select = SelectField(choices=[el for el in SUBJECTS.items()])
    submit = SubmitField('Выбрать задачу')