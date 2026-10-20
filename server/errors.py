"""Consistent, generic error responses (A02 / A09).

Clients only ever see a short message and a request id. Stack traces and internal
details are written to the server log under that request id instead.
"""
import logging

from flask import g, jsonify
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException

log = logging.getLogger("trendify")

GENERIC_MESSAGES = {
    400: "The request was not valid.",
    401: "Please sign in.",
    403: "You don't have permission to do that.",
    404: "Not found.",
    405: "Method not allowed.",
    409: "That conflicts with existing data.",
    413: "The upload is too large.",
    415: "Unsupported content type.",
    422: "The request could not be processed.",
    429: "Too many requests. Please slow down and try again shortly.",
    500: "Something went wrong on our side. Please try again.",
}


class ApiError(Exception):
    """Raise from anywhere in a request to return a JSON error."""

    def __init__(self, status, message=None, *, fields=None, code=None):
        super().__init__(message)
        self.status = status
        self.message = message or GENERIC_MESSAGES.get(status, "Error")
        self.fields = fields
        self.code = code


def _body(status, message, **extra):
    body = {"error": message, "request_id": g.get("request_id")}
    body.update({k: v for k, v in extra.items() if v is not None})
    return jsonify(body), status


def register_error_handlers(app):
    from database import db

    # A rejected request must never leave half-applied changes in the session (A09).
    # Anything that has to be kept (e.g. an audit entry for a failed login) is committed
    # explicitly before the error is raised.

    @app.errorhandler(ApiError)
    def handle_api_error(err):
        db.session.rollback()
        return _body(err.status, err.message, fields=err.fields, code=err.code)

    @app.errorhandler(ValidationError)
    def handle_validation_error(err):
        db.session.rollback()
        return _body(400, "Please check the highlighted fields.", fields=err.messages)

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        # Use our own wording, never the framework's (which can include internals).
        db.session.rollback()
        return _body(err.code or 500, GENERIC_MESSAGES.get(err.code, "Error"))

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        # Undo any half-finished database work so the data stays consistent (A09).
        db.session.rollback()
        log.exception("Unhandled error (request_id=%s)", g.get("request_id"))
        return _body(500, GENERIC_MESSAGES[500])
