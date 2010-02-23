import re, collections
from pytorqy.expression import *
from pytorqy.expression_shortname import BtN, L, LC, M, NM
#import pytorqy.treeseq as pt

def tokenize(text):
    return [ 'code' ] + [m.group() for m in re.finditer(r"(\d|[.])+|[-+*/%()]", text)]

def _parsing_expr_iter():    
    def to_recursive(expr): 
        assign_marker_expr(expr, '0', expr) 
        return expr
    
    # atomic
    parenv = BtN('v', Drop(L('(')) + [0,]*(Xcp(L(')')) + M('0')) + Drop(L(')')))
    numberv = BtN('v', Rex(r"^(\d|[.])"))
    yield Search(to_recursive(parenv | numberv | Any()))

    # unary +,-
    vSearch = NM('v', Search(M('0')))
    signv = BtN('v', (LC('+-')) + vSearch)
    yield to_recursive([0,1]*signv + [0,]*((vSearch + LC('+-')) | signv | Any()))
    
    # multiply, divide
    vSearch = NM('v', Search(M('0')))
    yield Search(to_recursive(BtN('v', vSearch + [1,]*(LC('*/%') + vSearch))))

    # add, sub
    vSearch = NM('v', Search(M('0')))
    yield Search(to_recursive(BtN('v', vSearch + [1,]*(LC('+-') + vSearch))))

parsing_exprs = list(_parsing_expr_iter())

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
    for expr in parsing_exprs:
        newSeq = expr.parse(seq)
        if newSeq is None: raise SystemError
        seq = newSeq
    #for L in pt.seq_pretty(seq): print(L) # prints an seq
    result = interpret(seq)
    print(result)
    