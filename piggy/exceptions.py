from flask import abort


class PiggyException(Exception):
    pass


class PiggyHTTPException(PiggyException):
    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code
        abort(status_code)
