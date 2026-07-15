"""
Shared Flask extension instances.

These are created here (unbound) and initialised against the app in app.py
via `extension.init_app(app)`. Keeping them in their own module avoids
circular imports between app.py, models.py and forms.py.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

# Where Flask-Login sends anonymous users who hit a @login_required route.
login_manager.login_view = "login"
login_manager.login_message = "Please log in to continue."
login_manager.login_message_category = "info"
