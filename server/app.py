"""Trendify API: Flask application factory."""
import logging
import uuid

from flask import Flask, g, jsonify, redirect, request
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from audit import configure_security_logging
from config import get_config
from errors import GENERIC_MESSAGES, register_error_handlers
from extensions import db, jwt, limiter, mail, migrate

log = logging.getLogger("trendify")

# Restrictive headers for a JSON API (A02 / A04). The frontend's own CSP is set where
# the frontend is served (see trendify-frontend/vite.config.ts).
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-site",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
}


def create_app(config_name=None):
    config = get_config(config_name)
    config.validate()

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config)
    app.config.setdefault("JWT_SECRET_KEY", None)
    if not app.config["JWT_SECRET_KEY"]:
        app.config["JWT_SECRET_KEY"] = app.config["SECRET_KEY"]

    if app.config["TRUSTED_PROXY_COUNT"]:
        n = app.config["TRUSTED_PROXY_COUNT"]
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=n, x_proto=n, x_host=n)

    logging.basicConfig(level=logging.DEBUG if app.debug else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    jwt.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    CORS(app, resources={r"/*": {
        "origins": app.config["CORS_ORIGINS"],
        "methods": ["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-CSRF-TOKEN", "Idempotency-Key"],
        "supports_credentials": True,
        "max_age": 600,
    }})

    if app.config["ENV_NAME"] == "production" and app.config["RATELIMIT_STORAGE_URI"].startswith("memory://"):
        log.warning("Rate limits are stored in memory; use RATELIMIT_STORAGE_URI=redis://... "
                    "when running more than one server process.")

    _register_jwt_callbacks()
    register_error_handlers(app)
    _register_request_hooks(app)
    _register_blueprints(app)
    configure_security_logging(app)

    from cli import register_cli
    register_cli(app)
    return app


def _register_jwt_callbacks():
    from models import RevokedToken, User

    @jwt.token_in_blocklist_loader
    def is_token_revoked(_header, payload):
        if RevokedToken.query.filter_by(jti=payload["jti"]).first():
            return True
        user = db.session.get(User, int(payload["sub"]))
        # Deactivated users and tokens from before a password change / logout-all are invalid.
        return user is None or not user.is_active or payload.get("tv") != user.token_version

    def _unauthorized(message, code):
        return jsonify(error=message, code=code, request_id=g.get("request_id")), 401

    jwt.unauthorized_loader(lambda reason: _unauthorized(GENERIC_MESSAGES[401], "not_signed_in"))
    jwt.invalid_token_loader(lambda reason: _unauthorized("Please sign in again.", "token_invalid"))
    jwt.expired_token_loader(lambda h, p: _unauthorized("Your session expired.", "token_expired"))
    jwt.revoked_token_loader(lambda h, p: _unauthorized("Please sign in again.", "token_revoked"))
    jwt.user_lookup_error_loader(lambda h, p: _unauthorized("Please sign in again.", "token_invalid"))


def _register_request_hooks(app):
    @app.before_request
    def assign_request_id():
        g.request_id = uuid.uuid4().hex[:16]

    @app.before_request
    def enforce_https():
        if app.config["FORCE_HTTPS"] and not request.is_secure and not app.testing:
            return redirect(request.url.replace("http://", "https://", 1), code=308)

    @app.after_request
    def add_security_headers(response):
        for name, value in SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        if request.is_secure or app.config["FORCE_HTTPS"]:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        if not request.path.startswith("/static/"):
            # Personal data must not be cached by browsers or shared proxies.
            response.headers["Cache-Control"] = "no-store"
        response.headers["X-Request-ID"] = g.get("request_id", "")
        return response


def _register_blueprints(app):
    from api.account import bp as account_bp
    from api.admin import bp as admin_bp
    from api.auth import bp as auth_bp
    from api.catalog import bp as catalog_bp
    from api.orders import bp as orders_bp

    for blueprint in (auth_bp, account_bp, catalog_bp, orders_bp, admin_bp):
        app.register_blueprint(blueprint)

    @app.get("/health")
    def health():
        return jsonify(status="ok")


if __name__ == '__main__':
    app = create_app()
    # Debug comes from the config profile (on for development only), never hardcoded (A02).
    app.run(host="127.0.0.1", port=5000, debug=app.config["DEBUG"])
