from typing import List
from tokens import Token

# exception at parse time
class ParseException(Exception): pass

# exception at lex time
class LexException(ParseException): pass

class UnidentifiedTokenException(ParseException):
    def __init__(self, token, message="Token unknown: '%s'"):
        super().__init__(message % token)
        self.message = message
        self.token = token

class InvalidSyntaxException(LexException):
    def __init__(self, stack: List[Token], message: str):
        from .mathlex import to_string
        s = to_string(stack)
        if s:
            s = f" Found near `{s}`"
        super().__init__(message + s)
        self.stack = stack
        self.message = message
