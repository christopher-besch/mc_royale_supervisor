from datetime import datetime
from mcuuid.api import GetPlayerData
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login


# user table
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    tutorial = db.Column(db.Boolean, default=True)
    is_supervisor = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)

    # mc data
    mc_name = db.Column(db.String(64))
    mc_uuid = db.Column(db.String(64))

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # function to get minecraft name and uuid
    def set_mc_data(self):
        player = GetPlayerData(self.username)
        if player.valid:
            self.mc_uuid = player.uuid
            self.mc_name = player.username
            return True
        else:
            return False

    # function to give this user supervisor privileges and remove them from everyone else
    def make_supervisor(self):
        # get every user
        users = User.query.all()
        # setting every users is_supervisor to False
        for user in users:
            user.is_supervisor = False
        # make this user supervisor
        self.is_supervisor = True
        # save changes
        db.session.commit()


# function to load current user in memory
@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
