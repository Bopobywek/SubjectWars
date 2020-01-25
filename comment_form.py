from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired


class CommentForm(FlaskForm):
    comment = StringField('Комментарий', validators=[DataRequired()])
    submit = SubmitField('Отправить')
