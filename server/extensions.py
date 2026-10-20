"""Flask extensions, created once and bound to the app in app.create_app()."""
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from flask_migrate import Migrate

from database import db

migrate = Migrate()
jwt = JWTManager()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)

__all__ = ["db", "migrate", "jwt", "mail", "limiter"]
