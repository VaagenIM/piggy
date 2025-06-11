from flask import abort


class PiggyException(Exception):
    pass


class PiggyErrorException(Exception):
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
