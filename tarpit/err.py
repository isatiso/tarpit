from tornado.web import HTTPError

__all__ = [
    'MissingArgumentError',
    'TokenExpiredError',
    'ArgumentTypeError',
    'InternalServerError',
    'AuthenticationError',
    'AuthorizationError',
    'ParseJSONError',
    'HTTPError',
    'ServiceError',
]


class MissingArgumentError(HTTPError):
    """Missing Argument Error."""

    def __init__(self, arg_name):
        super(MissingArgumentError, self).__init__(
            400, f'Missing argument "{arg_name}"')
        self.arg_name = arg_name


class TokenExpiredError(HTTPError):
    """Token Expired Error."""

    def __init__(self):
        super(TokenExpiredError, self).__init__(401, 'Token Expired')


class ArgumentTypeError(HTTPError):
    """Argument Type Error."""

    def __init__(self, arg_name, type_name):
        super(ArgumentTypeError, self).__init__(
            400, f'Argument "{arg_name}" should be {type_name}')


class InternalServerError(HTTPError):
    """Task Error."""

    def __init__(self, task_name, error_msg):
        super(InternalServerError, self).__init__(
            500, f'Error occured when excute task "{task_name}".\n{error_msg}')


class AuthenticationError(HTTPError):
    """Authentication Error."""

    def __init__(self, msg):
        super(AuthenticationError, self).__init__(401, msg)


class AuthorizationError(HTTPError):
    """Authorization Error."""

    def __init__(self, arg_name):
        super(AuthorizationError, self).__init__(
            401, f'User\'s "{arg_name}" not satisfied.')


class ParseJSONError(HTTPError):
    """Exception raised by `BaseHandler.parse_json`.

    This is a subclass of `HTTPError`, so if it is uncaught a 400 response
    code will be used instead of 500 (and a stack trace will not be logged).
    """

    def __init__(self, doc):
        super(ParseJSONError, self).__init__(400, f'ParseJSONError "{doc}"')


class ServiceError(Exception):

    def __init__(self, code, desc):
        self.code = code
        self.desc = desc
