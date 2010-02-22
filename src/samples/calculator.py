import re, collections
from pytorqy.expression import *
from pytorqy.expression_shortname import BtN, L, LC, M, NM
import pytorqy.treeseq as pt

def tokenize(text):
    return [ 'code' ] + [m.group() for m in re.finditer(r"(\d|[.])+|[-+*/%()]", text)]

def _parsing_expr_iter():    
    def to_recursive(expr): 
        assign_marker_expr(expr, '0', expr) 
        return expr
    
    # atomic
    parenv = BtN('v', Drop(L('(')) + [0,]*(Xcp(L(')')) + M('0')) + Drop(L(')')))
    numberv = BtN('v', Rex(r"^(\d|[.])"))
    yield Scan(to_recursive(parenv | numberv | Any()))

    # unary +,-
    vscan = NM('v', Scan(M('0')))
    signv = BtN('v', (LC('+-')) + vscan)
    yield to_recursive([0,1]*signv + [0,]*((vscan + LC('+-')) | signv | Any()))
    
    # multiply, divide
    vscan = NM('v', Scan(M('0')))
    yield Scan(to_recursive(BtN('v', vscan + [1,]*(LC('*/%') + vscan))))

    # add, sub
    vscan = NM('v', Scan(M('0')))
    yield Scan(to_recursive(BtN('v', vscan + [1,]*(LC('+-') + vscan))))

_parsing_exprs = list(_parsing_expr_iter())

def parse(seq):
    for expr in _parsing_exprs:
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        assert 1 + posDelta == len(seq)
        seq = [ seq[0] ] + outSeq
    return seq

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
            assert len(itemQ) == 1
            return interpret_i(itemQ.popleft()) * (-1.0 if i == '-' else 1.0)
        else:
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
    #print(seq) # prints tokens
    ast = parse(seq)
    #for L in pt.seq_pretty(ast): print(L) # prints an ast
    result = interpret(ast)
    print(result)
    