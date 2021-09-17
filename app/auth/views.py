from flask import render_template, redirect, request, url_for, flash
from flask_login import login_required, login_user, logout_user, current_user
from . import auth
from .. import db
from ..models import Owner
from ..email import send_email
from .forms import LoginForm, RegistrationForm, ChangeEmailForm, ChangePasswordForm, PasswordResetRequestForm, PasswordResetForm

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        owner = Owner(email=form.email.data.lower(),
                    owner_name=form.owner_name.data,
                    passcode = form.passcode.data,
                    phone = form.phone.data,
                    password='1234')
        
        db.session.add(owner)
        db.session.commit()
        flash("Your assigned password is '1234'. Log in and change your password!")
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        owner = Owner.query.filter_by(email=form.email.data.lower()).first()

        if owner is not None and owner.verify_password(form.password.data):
            
            try: login_user(owner, form.remember_me.data)
            except:print("Ameshindwa na log in")
            ###
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.homepage')
            #print('next->', next)
            return  redirect(url_for('main.homepage'))
            # return redirect(next)
        flash('Invalid email or password!')
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out!')
    return redirect(url_for('main.homepage'))

@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        if not current_user.confirmed and request.endpoint and request.blueprint != 'auth' and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.homepage'))
    return render_template('auth/unconfirmed.html')

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed: return redirect(url_for('main.homepage'))
    if current_user.confirm(token):
        db.session.commit()
        flash('You have confirmed your account. Thanks!')
    else: flash('The confirmation link is invalid or has expired')
    return redirect(url_for('main.homepage'))

@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account', 'auth/email/confirm', owner=current_user, token=token)
    flash('A new confirmation email has been sent to your email.')
    return redirect(url_for('main.homepage'))

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash('Your password has been updated.')
            return redirect(url_for('main.homepage'))
        else: flash('Invalid Password!')

    return render_template('auth/change_password.html', form=form)

@auth.route('/auth/reset', methods=['GET', 'POST'])
def password_reset_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.homepage'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        owner = Owner.query.filter_by(email=form.email.data.lower()).first()
        if owner:
            token = owner.generate_reset_token()
            send_email(owner.email, 'Reset Your Password', 'auth/email/reset_password', owner=owner, token=token)
        flash('An email with instructions to reset your password has been sent to you.')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', form=form)

@auth.route('/auth/reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.homepage'))
    form = PasswordResetForm()
    if form.validate_on_submit():
        if Owner.reset_password(token, form.password.data):
            db.session.commit()
            flash('Your password has been updated.')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.homepage'))
    return render_template('auth/reset_password.html', form=form)

@auth.route('/auth/change_email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data.lower()
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, 'Confirm your email address',
                       'auth/email/change_email',
                       owner=current_user, token=token)
            flash('An email with instructions to confirm your new email '
                  'address has been sent to you.')
            return redirect(url_for('main.homepage'))
        else:
            flash('Invalid email or password.')
    return render_template("auth/change_email.html", form=form)


@auth.route('/change_email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        db.session.commit()
        flash('Your email address has been updated.')
    else:
        flash('Invalid request.')
    return redirect(url_for('main.homepage'))