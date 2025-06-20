from io import StringIO
from mathlex import parse, lex, pprint, to_string
from tokens import OperatorToken, GroupToken, RegexToken, UnaryOperatorToken, UnaryPlacementType, LiteralToken, EOFToken

if __name__ == "__main__":
    # raw = input("> ")
    # raw = "y'-exp(x)*(sin(theta)+4))/ (e^x - 3*sin(14*y*pi)) * i^2 - inf"
    # raw = "4y'+3y+7x-67+5sin(15)-6x7162sin(5)12"
    raw = "y''+2y'+y=0"
    stream = StringIO(raw)
    parsed = parse(stream)
    lexed = lex(parsed)
    pprint(lexed)           # formatted color output
    print(to_string(lexed)) # explicit plain text output

    def preprocess(T):
        has_eq = False
        implicit_diff = 0
        def rec(T):
            nonlocal has_eq, implicit_diff
            v = set()
            f = set()
            lv = None
            for i,t in enumerate(T):
                if isinstance(t, OperatorToken):
                    if t.name.startswith("'"):
                        implicit_diff += 1
                        f.add(lv)
                        v.remove(lv)
                    if t.name == "=":
                        has_eq = True
                if isinstance(t, GroupToken):
                    if t.value:
                        V,F = rec(t.value)
                        f |= F
                        v |= V
                else:
                    if isinstance(t, RegexToken) and t.name == "variable":
                        v.add(t.value)
                        lv = t.value
            return v,f
        v,f = rec(T)
        v = list(v)
        f = list(f)
        for i in f:
            while i in v:
                v.remove(i)
        if implicit_diff > 0:
            if len(v) > 1:
                print("# Warning: Implicit differentiation with multiple variables detected, manual intervention is required.")
            if len(v) == 0:
                if "t" not in v:
                    v.append("t")
                elif "x" not in v:
                    v.append("x")
                elif "y" not in v:
                    v.append("y")
                else:
                    v.append("_depend_var")
        return v, f, has_eq

    variables, functions, is_equation = preprocess(lexed)

    def r(T):
        global variables, is_equation
        cvar = None
        for i,t in enumerate(T):
            if isinstance(t, GroupToken):
                if t.name:
                    print(f"sp.{t.name.replace('arc', 'a')}", end="")
                print(t.boundary_start, end="")
                if t.value:
                    r(t.value)
                print(t.boundary_end, end="")
            else:
                match t:
                    case UnaryOperatorToken():
                        if not cvar:
                            raise ise(T, "Floating unary operator: {t.name}")
                        if t.name =="!":
                            print("sp.factorial({cvar.value})", end="")
                        if t.name.startswith("'"):
                            print(f"{cvar.value}.diff({dv}, {len(t.name)})", end="")
                            cvar = None
                    case OperatorToken():
                        if t.name == "=":
                            print("\nrhs = ", end="")
                        else:
                            print(t, end="")
                    case LiteralToken():
                        print(f"sp.{t.name}", end="")
                    case RegexToken():
                        if i+1 in range(len(T)):
                            if isinstance(T[i+1], UnaryOperatorToken):
                                if T[i+1].placement == UnaryPlacementType.POSTFIX:
                                    cvar = t
                        if not cvar:
                            print(t.value, end="")
                    case EOFToken():
                        print()

    from print_to_string import print_to_string as pts
    with pts() as sio:
        print("import sympy as sp")
        if is_equation:
            print("from sympy import Eq")
        print()
        print(", ".join(variables) + " = sp.symbols('"+ " ".join(variables) + "')")
        dv = "_depend_var"
        if len(variables) == 1:
            dv = variables[0]
        for fun in functions:
            print(fun + " = sp.Function('"+ fun +"')(" + dv + ")")
        if is_equation:
            print("lhs = ", end="")
        r(lexed)
        if is_equation:
            print("lhs = sp.simplify(lhs)")
            print("rhs = sp.simplify(rhs)")
            print("sp.pprint(Eq(lhs, rhs))")
            print("print()")
            if len(functions) > 0:
                print("result = sp.dsolve(Eq(lhs, rhs), " + ", ".join(functions) + ")")
            else:
                print("result = sp.solve(Eq(lhs, rhs), " + ", ".join(variables) + ")")
            print("sp.pprint(result)")


    with open("test.py", "w") as f:
        f.write(sio.getvalue())
    print("::: Results :::")
    exec(sio.getvalue(), {})