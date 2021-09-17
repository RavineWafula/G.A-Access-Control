from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, ValidationError
from wtforms.fields.core import BooleanField
from wtforms.fields.simple import PasswordField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp

from ..models import Owner

class RegistrationForm(FlaskForm):
    owner_name = StringField('Full Name', validators=[DataRequired(), Length(1, 60)])
    email = StringField('Email', validators=[DataRequired(), Length(1, 60), Email(), EqualTo('email2', message='Email must match!')])
    email2 = PasswordField('Confirm Email', validators=[DataRequired()])
    phone = StringField('Phone Number eg 254700000000', validators=[DataRequired(), Length(12), Regexp('^[0-9]*$', 0,'Phone number must have only numbers')])
    passcode = PasswordField('Passcode', validators=[DataRequired(), EqualTo('passcode2', message='Passcodes must match!')])
    passcode2 = PasswordField('Confirm Passcode', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if Owner.query.filter_by(email=field.data.lower()).first():
            raise ValidationError("Email already registered!")

    #def validate_name(self, field):
    #    if User.query.filter_by(name=field.data).first():
    #        raise ValidationError("Name already in use!")

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 60), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log in')

class ChangeEmailForm(FlaskForm):
    email = StringField('New Email', validators=[DataRequired(), Length(1, 60), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField("Update Email Address")

    def validate_email(self, field):
        if Owner.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('Email already registered!')

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old password', validators=[DataRequired()])
    password = PasswordField('New password', validators=[DataRequired(), EqualTo('password2', message='Passwords must match!')])
    password2 = PasswordField('Confirm new password',validators=[DataRequired()])
    submit = SubmitField('Update Password')

class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),Email()])
    submit = SubmitField('Reset Password')

class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), EqualTo('password2', message='Passwords must match!')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Reset Password')
