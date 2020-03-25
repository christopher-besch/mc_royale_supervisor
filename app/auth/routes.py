from flask import render_template, flash, redirect, url_for
from flask_login import login_user, logout_user, current_user, login_required
from app.auth import bp
from app import db
from app.forms import LoginForm, PasswordChangeForm
from app.models import User


# login
@bp.route('/login', methods=['GET', 'POST'])
def login():
    # only unauthorised users can log in
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('main.index'))
    return render_template('login.html', title='Sign In', form=form)


# logout
@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


# change the users password
@bp.route('/password_change/<username>', methods=['GET', 'POST'])
@login_required
def password_change(username):
    # only an admin and the user who needs the password change is allowed
    if not current_user.is_admin and current_user.username != username:
        return redirect(url_for('main.index'))

    # when the user does not exist, the password can not be changed
    user = User.query.filter_by(username=username).first()
    if user is None:
        return redirect(url_for('main.index'))

    # creating the form
    form = PasswordChangeForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('The password of {} has been changed'.format(username))
        # redirecting after change
        if current_user.username == username:
            return redirect(url_for('auth.logout'))
        else:
            return redirect(url_for('main.admin'))
    return render_template('password_change.html', form=form, username=username, title='Password Change')
