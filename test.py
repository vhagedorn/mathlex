import sympy as sp
from sympy import Eq

t = sp.symbols('t')
y = sp.Function('y')(t)
lhs = y.diff(t, 2) + 2 * y.diff(t, 1) + y
rhs = 0
lhs = sp.simplify(lhs)
rhs = sp.simplify(rhs)
sp.pprint(Eq(lhs, rhs))
print()
result = sp.dsolve(Eq(lhs, rhs), y)
sp.pprint(result)
