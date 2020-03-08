from flask import Blueprint

# create blueprint
bp = Blueprint('auth', __name__, template_folder='templates')

# load other scripts
from app.auth import routes
