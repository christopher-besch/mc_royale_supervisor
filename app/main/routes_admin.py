from flask import render_template, redirect, url_for, flash, jsonify, request
from flask_login import current_user, login_required
from app import db, match
from app.main import bp
from app.models import User
from app.forms import RegistrationForm


# admin page
@bp.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    # only an admin is allowed
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    # creating registration form
    form = RegistrationForm()
    if form.validate_on_submit():
        # create user
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        user.set_mc_data()
        db.session.add(user)
        db.session.commit()
        print(user.mc_uuid)
        flash('The account \"{}\" has been created!'.format(user.username))
        return redirect(url_for('main.admin'))

    users = User.query.order_by(User.id)
    return render_template('admin.html', title="Admin Page", users=users, form=form, match=match)


# make supervisor (ajax)
@bp.route('/make_supervisor', methods=['POST'])
@login_required
def make_supervisor():
    # only an admin is allowed and only when the match isn't already running
    if not current_user.is_admin or match.running:
        return redirect(url_for('main.index'))

    # searching for user
    user = User.query.filter_by(username=request.form['username']).first()

    # only when the user exists
    if user:
        # make supervisor
        user.make_supervisor()
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})


# change admin state (ajax)
@bp.route('/change_admin_state', methods=['POST'])
@login_required
def change_admin_state():
    # only an admin is allowed
    if not current_user.is_admin:
        return redirect(url_for('main.index'))

    # searching for user
    user = User.query.filter_by(username=request.form['username']).first()

    # only when the user exists
    if user:
        # change admin state
        if request.form['new_state'] == "true":
            user.is_admin = True
        else:
            user.is_admin = False
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})


# delete user
@bp.route('/delete/<username>')
@login_required
def delete(username):
    # only an admin is allowed
    if not current_user.is_admin:
        return redirect(url_for('main.index'))

    # searching for the user
    user = User.query.filter_by(username=username).first()
    # only when the user exists and it is not the one currently logged in
    if user and user.username != current_user.username:
        return render_template('delete.html', user=user, title='Delete User')
    else:
        return redirect(url_for('main.admin'))


# actually deleting an account (ajax)
@bp.route('/confirmed_delete', methods=['POST'])
@login_required
def confirmed_delete():
    # only an admin is allowed
    if not current_user.is_admin:
        return redirect(url_for('main.index'))
    # searching for user
    user = User.query.filter_by(username=request.form['username']).first()
    if user and user.username != current_user.username:
        # deleting the user
        db.session.delete(user)
        db.session.commit()
        flash('{} has been deleted!'.format(user.username))
        return jsonify({'success': True})
    return jsonify({'success': False})
