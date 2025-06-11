from flask import abort
from werkzeug.exceptions import HTTPException

# For consistency between HTTPException and PiggyHTTPException
DEFAULT_ERROR_MESSAGE_NAMES = {
    "404": "Page not found",  # vs just "Not Found"
}

ERROR_MESSAGE_DESCRIPTIONS = {
    "default": "Something went wrong, please try again later.",
    "404": "Your <strike>queen</strike> gilt is in another castle...",
}


def normalize_http_exception(e):
    """Convert any (HTTPException) exception to a usable PiggyHTTPException."""
    if not any(isinstance(e, exc) for exc in (HTTPException, PiggyHTTPException)):
        # TODO: We shouldn't get here, but if we do, log the error
        return PiggyHTTPException("An unexpected error occurred", status_code=500)

    if isinstance(e, HTTPException):
        name = DEFAULT_ERROR_MESSAGE_NAMES.get(str(e.code), e.name)
        return PiggyHTTPException(name, status_code=e.code)

    return e


class PiggyException(Exception):
    pass


class PiggyErrorException(PiggyException):
    pass


class PiggyHTTPException(PiggyException):
    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code
        self.raised_in_try_except = False

    def __raise__(self):
        if not self.raised_in_try_except:
            abort(self.status_code)
        else:
            raise self

    def __enter__(self):
        self.raised_in_try_except = True

    def __exit__(self, exc_type, exc_value, traceback):
        self.raised_in_try_except = False
