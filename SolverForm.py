from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextField
from wtforms.validators import DataRequired


class SolverForm(FlaskForm):
    answer = StringField(validators=[DataRequired()])
    submit = SubmitField('Проверить решение')
