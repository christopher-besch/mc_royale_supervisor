from app import db
from app.models import User

username = input('username of the new admin: ')
password = input('new admin password: ')
password2 = input('repeat new admin password: ')

# get admin user if already existent
user = User.query.filter_by(username=username).first()
if password2 == password and user is None:
    # create user
    user = User(username=username)
    user.set_password(password)
    user.is_admin = True
    user.set_mc_data()
    db.session.add(user)
    db.session.commit()

    print('The admin account was successfully created!')
else:
    print('An error occurred!')
