from app import db
from app.models import User

password = input('new password:')
password2 = input('repeat new password:')

user = User.query.filter_by(username='admin').first()
if password2 == password and user is not None:
    user.set_password(password)
    db.session.commit()
    print('The password of the admin account has been changed successfully!')
else:
    print('An error occurred!')
