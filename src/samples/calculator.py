import re, collections
import pyrem_torq
from pyrem_torq.expression import *

BtN = BuildToNode
L = Literal
LC = LiteralClass
NM = NodeMatch

def tokenize(text):
    return [ 'code' ] + [m.group() for m in re.finditer(r"(\d|[.])+|[-+*/%()]", text)]

def _build_parsing_exprs():    
    r = []
    
    # atomic
    expr0 = Holder()
    parenV = BtN('v', Drop(L('(')) + [0,None]*(RequireBut(L(')')) + expr0) + Drop(L(')')))
    numberV = BtN('v', Rex(r"^(\d|[.])"))
    expr0.expr = parenV | numberV | Any()
    r.append(Search(expr0.expr))

    # unary +,-
    expr0 = Holder()
    vSearch = NM('v', Search(expr0))
    signV = BtN('v', (LC('+-')) + vSearch) + [0,1]*LC('+-')
    expr0.expr = [0,1]*signV + [0,None]*((vSearch + [0,1]*LC('+-')) | signV | vSearch | Any())
    r.append(expr0.expr)
    
    # multiply, divide
    expr0 = Holder()
    vSearch = NM('v', Search(expr0))
    expr0.expr = BtN('v', vSearch + [1,None]*(LC('*/%') + vSearch)) | vSearch
    r.append(Search(expr0.expr))

    # add, sub
    expr0 = Holder()
    vSearch = NM('v', Search(expr0))
    expr0.expr = BtN('v', vSearch + [1,None]*(LC('+-') + vSearch)) | vSearch
    r.append(Search(expr0.expr))
    
    return r

parsing_exprs = _build_parsing_exprs()

def interpret(ast):
    _opstr_to_func = { '+' : float.__add__, '-' : float.__sub__, 
        '*' : float.__mul__, '/' : float.__truediv__, '%' : float.__mod__ }
    def interpret_i(nodeOrItem):
        if isinstance(nodeOrItem, str): 
            return float(nodeOrItem)
        # nodeLabel = nodeOrItem[0] # nodeLabel will be 'code' or 'v'
        itemQ = collections.deque(nodeOrItem[1:])
        i = itemQ.popleft()
        if i in ('+', '-'): # unary +,-
            # op, value
            assert len(itemQ) == 1
            return interpret_i(itemQ.popleft()) * (-1.0 if i == '-' else 1.0)
        else:
            # value, op, value, op value, ...
            value = interpret_i(i)
            while itemQ:
                op = itemQ.popleft()
                right = interpret_i(itemQ.popleft())
                value = _opstr_to_func[op](value, right)
            return value
    return interpret_i(ast)

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) == 1:
        print("""
usage: calculator <expr>
  A simple calculator. <expr> must consist of floating-point numbers and 
  operators: +,-,*,/,%,(). For example, "1 + 2 * (-3) - 4 * (5 - 6) * -7".
"""[1:-1])
        sys.exit(0)
    
    text = " ".join(sys.argv[1:])
    seq = tokenize(text)
    for expr in parsing_exprs:
        for L in pyrem_torq.treeseq.seq_pretty(seq): print L # prints an seq
        newSeq = expr.parse(seq)
        if newSeq is None: raise SystemError
        seq = newSeq
    for L in pyrem_torq.treeseq.seq_pretty(seq): print L # prints an seq
    result = interpret(seq)
    print result
    