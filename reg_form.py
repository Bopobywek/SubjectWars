from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email


class RegForm(FlaskForm):
    username = StringField('Login', validators=[DataRequired(), Length(3, 15)])
    password = PasswordField('Password', validators=[DataRequired(), Length(6, 25,
                                                                            message="Длина пароля должна быть"
                                                                                    " от 6 до 25 символов")])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Register')
