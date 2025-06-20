from io import StringIO
from typing import List

from tokens import (
    Token, EOFToken, LiteralToken, RegexToken, OperatorToken,
    UnaryOperatorToken, GroupBoundaryToken, GroupToken, FunctionToken,
    UnaryPlacementType, BoundaryType
)
from exceptions import UnidentifiedTokenException as ute, InvalidSyntaxException as ise

var_token = RegexToken("variable", r"^[a-zA-Z][a-zA-Z0-9_]*$")
tokens = [
    RegexToken("number", r"^\d+(\.\d*)?$"),
    OperatorToken("^").with_value(None, fmt="{name}"), # dense operator
    var_token,
] + [ 
    LiteralToken(t) for t in ['pi', 'e', 'i', 'inf'] 
] + [
    FunctionToken(t) for t in ['exp', 'ln', 'sin', 'cos', 'tan', 'sec', 'csc', 'cot', 'arcsin', 'arccos', 'arctan', 'sinh', 'tanh', 'cosh', 'sech', 'csch', 'coth', 'arcsinh', 'arccosh', 'arctanh']
] + [
    GroupBoundaryToken(t, BoundaryType.START) for t in '({['
] + [
    GroupBoundaryToken(t, BoundaryType.END) for t in ')}]'
] + [
    OperatorToken(t) for t in '+-*/%='
# ] + [
#     UnaryOperatorToken(t, UnaryPlacementType.PREFIX) for t in '+-'
] + [
    UnaryOperatorToken(t, UnaryPlacementType.POSTFIX) for t in ["'", "''", "'''", "!"]
]

def parse(stream: StringIO):
    parsed = list()

    tok = ""
    greedy = False
    while (s := stream.read(1)):
        if not s.strip():
            continue

        tok += s
        matches = [t for t in tokens if t.partialmatch(tok)]
    
        wasgreedy = False
        if greedy:
            if not matches:
                matches = [t for t in tokens if t.fullmatch(tok[:-1])]
                tok = tok[:-1]
                stream.seek(stream.tell() - 1)
                greedy = False
                wasgreedy = True
                # backtrack after greedy

        def check_eof():
            if stream.read(1) != "":
                stream.seek(stream.tell() - 1)
                return False 
            return True

        if matches:
            if any(m.greedy for m in matches):
                if not wasgreedy:
                    if not check_eof():
                        greedy = True
                        continue
            
            if len(matches) > 1:
                if check_eof():
                    matches = [t for t in tokens if t.fullmatch(tok)]
                if len(matches) > 1 and var_token in matches:
                    matches.remove(var_token)
                if len(matches) > 1:
                    raise ute(tok, f"Ambiguous token: '%s' matches multiple tokens: {matches}")

            match = matches.pop()
            parsed.append(match.with_value(tok))
            tok = ""
            continue
        if not any(t.fullmatch(tok) if check_eof() else t.partialmatch(tok) for t in tokens):
            raise ute(tok)
        
    parsed.append(EOFToken())
    return parsed

def lex(parsed: List[Token]):
    def recurse(it, fr=False):
        lexed = list()

        def check_implicit_mult(cg):
            nonlocal lexed
            if lexed:
                t1 = lexed[-1]
                t2 = cg
                # conditions for implicit multiplication:
                # - neither t1 or t2 are EOF/Operator tokens
                # - t1 and t2 are not adjacent Group/GroupBoundary tokens
                if (
                    not isinstance(t1, EOFToken)
                    and not isinstance(t2, EOFToken)
                    and not isinstance(t1, OperatorToken)
                    and not isinstance(t2, OperatorToken)
                    and not (isinstance(t1, GroupToken) and isinstance(t2, GroupBoundaryToken))
                    and not (isinstance(t2, GroupToken) and isinstance(t1, GroupBoundaryToken))
                ):
                    lexed.append(OperatorToken("*"))
                    print(f"Applying implicit multiplication to adjacent tokens: {t1} and {t2}")

        curr_group = None
        eq_ct = 0
        while (p := next(it, None)) is not None:
            if isinstance(p, OperatorToken) and p.name == "=":
                if not fr or curr_group:
                    raise ise(lexed, "Misplaced assignment operator. Assignment operators are only allowed in a top level expression.")
                eq_ct += 1
            if eq_ct > 1:
                raise ise(lexed, "Multiple assignment operators detected. Only one assignment operator per expression is allowed.")
            if isinstance(p, GroupToken):
                curr_group = p.with_value(None)
            if curr_group:
                if isinstance(p, GroupBoundaryToken):
                    if p.bt == BoundaryType.START:
                        curr_group.boundary_start = p
                        v,c = recurse(it)
                        curr_group.value = v
                        curr_group.boundary_end = c
                        check_implicit_mult(curr_group)
                        lexed.append(curr_group)
                        curr_group = None
                    else:
                        raise ise(lexed, f"Unexepcted end boundary token: {p}")
                else:
                    if not curr_group.value:
                        curr_group.value = list()
                    curr_group.value.append(p)
                    continue
            else:
                if isinstance(p, GroupBoundaryToken):
                    if p.bt == BoundaryType.START:
                        # create implicit group
                        implicit = GroupToken("")
                        implicit.boundary_start = p
                        v,c = recurse(it)
                        implicit.value = v
                        implicit.boundary_end = c
                        check_implicit_mult(implicit)
                        lexed.append(implicit)
                    if p.bt == BoundaryType.END:
                        if fr:
                            continue
                        else:
                            return lexed,p
                else:
                    check_implicit_mult(p)
                    lexed.append(p)
            if isinstance(p, EOFToken):
                return lexed, p

        raise ise(lexed, "Unexpected end of input at lex time. Did you forget to close a group?")

    if not parsed or not isinstance(parsed[-1], EOFToken):
        raise ise(parsed, "Expected EOF token at the end of the input.")
    it = parsed.__iter__()
    lexed, eof = recurse(it,fr=True)

    return lexed

def to_string(tokens: List[Token]):
    return "".join([str(t) for t in tokens])
            
def pprint(tokens: List[Token]):
    from rich.console import Console
    from rich.text import Text

    def get_style(token):
        match token:
            case UnaryOperatorToken():
                return "white"
            case OperatorToken():
                return "white"
            case GroupBoundaryToken():
                return "bold dim"
            case FunctionToken():
                return "bold green"
            case RegexToken():
                if token.name == "number":
                    return "red"
                if token.name == "variable":
                    return "blue"
            case LiteralToken():
                return "green"
            case EOFToken():
                return "reset"
        return "white"

    console = Console()
    def print_tokens(tokens):
        for t in tokens:
            if isinstance(t, GroupToken):
                if t.name:
                    console.print(Text(t.name, style=get_style(t)), end="")
                if t.boundary_start:
                    console.print(Text(str(t.boundary_start), style=get_style(t.boundary_start)), end="")
                if t.value:
                    print_tokens(t.value)
                if t.boundary_end:
                    console.print(Text(str(t.boundary_end), style=get_style(t.boundary_end)), end="")
            else:
                if t.name != "*":
                    console.print(Text(str(t), style=get_style(t)), end="")
    print_tokens(tokens)
    console.print()  # newline