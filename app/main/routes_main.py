from datetime import datetime
from flask import render_template, redirect, url_for, jsonify, request
from flask_login import current_user, login_required
from app import db
from app.main import bp


# save last seen time
@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


# start page (only reroute hub)
@bp.route('/')
@bp.route('/index')
@login_required
def index():
    # tutorial page
    if current_user.tutorial:
        return redirect(url_for('main.tutorial'))
    # supervisor page
    elif current_user.is_supervisor:
        return redirect(url_for('main.supervisor'))
    # default = overview page
    else:
        return redirect(url_for('main.overview'))


# tutorial page
@bp.route('/tutorial')
@login_required
def tutorial():
    return render_template('tutorial.html', title='Tutorial')


# changing tutorial state (ajax)
@bp.route('/change_tutorial_state', methods=['POST'])
@login_required
def change_tutorial_state():
    current_user.tutorial = request.form['new_state'] == 'true'
    db.session.commit()
    return jsonify({'success': True})


# supervisor page
@bp.route('/supervisor')
@login_required
def supervisor():
    # only supervisors can enter this page
    if not current_user.is_supervisor:
        return redirect(url_for('main.index'))

    return render_template('supervisor.html', title='Supervisor Page')


# overview page for every other user
@bp.route('/overview')
@login_required
def overview():
    return render_template('overview.html', title='Supervisor Page')
