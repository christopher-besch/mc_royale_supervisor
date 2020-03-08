from app import db
from app.models import User

password = input('password:')
password2 = input('repeat password:')

user = User.query.filter_by(username='admin').first()
if password2 == password and user is None:
    # create user
    user = User(username='admin')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    print('The admin account was successfully created!')
else:
    print('An error occurred!')
