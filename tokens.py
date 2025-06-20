from abc import ABC, abstractmethod
import re
import copy
from enum import Enum

class Token(ABC):
    def __init__(self, name, fmt, value=None, greedy=False):
        self.name = name
        self.fmt = fmt
        self.value = value
        self.greedy = greedy

    def __repr__(self):
        repr = self.__class__.__name__
        repr += "("
        repr += f"`{self.name}`"
        if self.value is not None:
            repr += f", {self.value}"
        repr += ")"
        return repr

    def __str__(self):
        F = self.__dict__.copy()
        if "value" in F and isinstance(F["value"], list):
            F["value"] = "".join(str(v) for v in F["value"])
        return self.fmt.format(**F)
    
    def with_value(self, value, **kwargs):
        clone = copy.copy(self)
        if value != clone.name:
            clone.value = value
        for k, v in kwargs.items():
            setattr(clone, k, v)
        return clone

    @abstractmethod
    def fullmatch(self, token): pass

    @abstractmethod
    def partialmatch(self, token): pass

class EOFToken(Token):
    def __init__(self):
        super().__init__("", "", greedy=False)

    def fullmatch(self, token): return False

    def partialmatch(self, token): return False

    def with_value(self, value, *args, **kwargs): return self

class LiteralToken(Token):
    def __init__(self, name):
        super().__init__(name, "{name}", greedy=True)

    def fullmatch(self, token):
        return token == self.name
    
    def partialmatch(self, token):
        return self.name.startswith(token)

class RegexToken(Token):
    def __init__(self, name, pattern, value=None):
        super().__init__(name, "{value}", value, greedy=True)
        self.pattern = re.compile(pattern)

    def fullmatch(self, token):
        return self.pattern.match(token)
    
    def partialmatch(self, token): return self.fullmatch(token)

class OperatorToken(LiteralToken):
    def __init__(self, name):
        super().__init__(name)
        self.fmt = " {name} "

class UnaryPlacementType(Enum):
    PREFIX = 1
    POSTFIX = 2

class UnaryOperatorToken(OperatorToken):
    def __init__(self, name, placement: UnaryPlacementType):
        super().__init__(name)
        if placement == UnaryPlacementType.PREFIX:
            self.fmt = " {name}"
        if placement == UnaryPlacementType.POSTFIX:
            self.fmt = "{name}"
        self.placement = placement

class BoundaryType(Enum):
    START = 1
    END = 2

class GroupBoundaryToken(LiteralToken):
    def __init__(self, name, bt: BoundaryType):
        super().__init__(name)
        self.bt = bt

class GroupToken(Token):
    def __init__(self, name, value=None):
        super().__init__(name, "{name}{boundary_start}{value}{boundary_end}", value)
        self.boundary_start = None
        self.boundary_end = None

    def fullmatch(self, token):
        return token == self.name
    
    def partialmatch(self, token):
        return self.name.startswith(token.lower())

class FunctionToken(GroupToken):
    def __init__(self, name, value=None):
        super().__init__(name, value)
        self.greedy = True
