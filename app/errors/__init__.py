from flask import Blueprint

# create blueprint
bp = Blueprint('errors', __name__, template_folder='templates')

# load other scripts
from app.errors import handlers
