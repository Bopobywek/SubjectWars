from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField

class CreateTaskform():
    title = StringField('Title')
    body = TextAreaField('Body')