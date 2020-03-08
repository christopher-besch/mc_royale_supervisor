from flask import Blueprint

# create blueprint
bp = Blueprint('main', __name__, template_folder='templates')

# load other scripts
from app.main import routes
