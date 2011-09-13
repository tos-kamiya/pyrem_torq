# tinyawk
# an interpreter of a extremely small subset of AWK programming language.
# supported reserved words are:
#   BEGIN END NF NR if else next print while
#   ( ) [ ] { } ; , < <= > >= == != && || ! - + * / % $
# note that: 
# - escape sequences in string are not supported.
# - regular expression is Python's one.
# - all numbers are integers, no floating points.
# - assignment to NF, NR or $* is undefined behavior.

from pyrem_torq import *
from pyrem_torq.expression import *

def split_to_str(text):
    p = "|".join([
        r"/[^/\r\n]*/", r'"[^"\r\n]*"', r"\d+", # literals (regex, string, integer)
        r"#[^\r\n]*", # comment
        r"[ \t]+", r"\r\n|\r|\n", # white spaces, newline
        r"[a-zA-Z_](\w|_)*", # identifier
        r"[<>!=]=|&&|[|][|]", r"[-+*/%<>!=()${},;]|\[|\]", # operators
        r"." # invalid chars
    ])
    return [ 'code' ] + [m.group() for m in re.finditer(p, text)]

def tokenizing_expr_iter():
    # identify reserved words, literals, identifiers
    e = Search(script.compile(r"""
    (r_BEGIN <- "BEGIN") | (r_END <- "END")
    | (r_next <- "next") | (r_print <- "print") | (r_if <- "if") | (r_else <- "else") | (r_while <- "while")
    | (id <- r"^[a-zA-Z_]") 
    | (l_integer <- r"^[0-9]") | (l_string <- r"^\"") | (l_regex <- r"^/")
    | (op_gt <- ">") | (op_ge <- ">=") | (op_lt <- "<") | (op_le <- "<=") | (op_ne <- "!=") | (op_eq <- "==")
    | (op_and <- "&&") | (op_or <- "||")
    | (op_plus <- "+") | (op_minus <- "-") | (op_mul <- "*") | (op_div <- "/") | (op_mod <- "%")
    | (op_assign <- "=") | (op_not <- "!") | (op_dollar <- "$")
    | (LP <- "(") | (RP <- ")") | (LB <- "{") | (RB <- "}") | (LK <- "[") | (RK <- "]")
    | (comma <- ",") | (semicolon <- ";")
    | (newline <- "\r\n" | "\r" | "\n")
    | (null <- r"^[ \t#]")
    | any, error("unexpected character")
    ;"""))
    yield "identify reserved words, literals, identifiers", e
    
    # identify statement-terminating new-line chars
    e = Search(script.compile(r"""
    (comma | LB | op_or | op_and | r_else), (null <- newline)
    ;"""))
    yield "remove neglected new-line characters", e

def stmt_parsing_expr_iter():
    # parse pattern-actions and blocks.
    stmtLevelBlock = script.compile("""
    (block <- (null <- LB), *(req^(RB), @0), (newline <-), (null <- RB))  
        # '}' can be a terminator of a statement, so insert a dummy new-line just before '}'
    | any
    ;""")
    actionLevelBlock = script.compile(r"""
    (pa <- 
        ((r_BEGIN | r_END) | (expr_empty <-)),
        (block <- (null <- LB), *(req^(RB), @stmtLevelBlock), (newline <-), (null <- RB)), 
        (null <- newline))
    | (pa <- 
        (expr <- +any^(LB | newline)), 
        ((block <- (null <- LB), *(req^(RB), @stmtLevelBlock), (newline <-), (null <- RB)) | (block_empty <-)),
        (null <- newline))
    | (null <- newline)
    ;""", replaces={ 'stmtLevelBlock' : stmtLevelBlock })
    e = [0,None] * actionLevelBlock
    yield "parse pattern-actions and blocks", e
    
    # parse statements
    getSimpleStmt = script.compile(r"""
    (stmt <- 
        (r_null_statement <-), semicolon 
        | (r_print_empty <- r_print), (semicolon | newline)
        | r_print, (expr <- +any^(semicolon | newline)), (semicolon | newline)
        | r_print, error("invalid print statement")
        | r_next, (semicolon | newline)
        | r_next, error("invaild 'next' statement")
        | (expr <- +any^(semicolon | newline)), (semicolon | newline))
    ;""")
    e = Search(script.compile(r"""
    (stmt <- 
        (r_if, (null <- LP), (expr <- +any^(newline | RP)), (null <- RP), ?(null <- newline), ((block :: ~@0) | @getSimpleStmt),
        *((r_elif <- r_else, r_if), (null <- LP), (expr <- +any^(newline | RP)), (null <- RP), ?(null <- newline), ((block :: ~@0) | @getSimpleStmt)),
        ?(r_else, ((block :: ~@0) | @getSimpleStmt))))
    | r_if, error("invalid 'if' statement") | r_else, error("'else' doesn't have a matching 'if'") 
    | (stmt <- r_while, (null <- LP), (expr <- +any^(newline | RP)), (null <- RP), ((block :: ~@0) | @getSimpleStmt))
    | r_while, error("invalid 'while' statement")
    | @getSimpleStmt
    | (null <- newline)
    | (block :: ~@0) 
    | (pa :: (r_BEGIN | r_END | expr_empty | expr), (block :: ~@0))
    | any, error("unexpected token")
    ;""", replaces={ 'getSimpleStmt' : getSimpleStmt }))
    yield "parse statements", e
    
def expr_parsing_expr_iter():
    def operator_parser_iter():
        n = Node
        kit = extra.operator_builer.OperatorBuilder()
        kit.atomic_term_expr = Or(n("l_integer"), n("l_string"), n("l_regex"), n("id"))
        kit.composed_term_node_labels = ( "expr", )
        kit.generated_term_label = "expr"
        
        yield "paren", kit.build_O_expr(( Drop(n("LP")), Drop(n("RP")) ))
        # Drop parentheses chars
        
        yield "index", kit.build_tO_expr(( n("LK"), n("RK") ))
        yield "unary ops", kit.build_Ot_expr(n("op_minus"), n("op_plus"), n("op_not"), n("op_dollar"))
        yield "binary mul/div", kit.build_tOt_expr(n("op_mul"), n("op_div"), n("op_mod"))
        yield "binary add/sub", kit.build_tOt_expr(n("op_minus"), n("op_plus"))
        
        yield "binary string concatenate", kit.build_tOt_expr(InsertNode("op_cat"))
        # The concatenation operator is epsilon, so that insert a token 'op_cat' where the operator appears
        
        yield "binary compare ops", kit.build_tOt_expr(\
                n("op_gt"), n("op_ge"), n("op_lt"), n("op_le"), n("op_ne"), n("op_eq"))
        yield "binary logical-and", kit.build_tOt_expr(n("op_and"))
        yield  "binary logical-or", kit.build_tOt_expr(n("op_or"))
        yield  "comma", kit.build_tOt_expr(n("comma"))
        yield  "binary assign op", kit.build_tOt_expr(n("op_assign"))
    for desc, eParser in operator_parser_iter():
        e = Search(script.compile("""(expr :: @eParser)
        | (stmt :: ~@0) | (block :: ~@0) | (pa :: ~@0)
        ;""", replaces={ "eParser" : eParser }))
        yield "expression " + desc, e
    
    yield "remove redundant paren", Search(script.compile("""
    req(expr :: expr | l_integer | l_string | l_regex | id), (<>expr :: @0)
    | (expr :: id, LK, *(req^(RK), @0), RK) 
    | (expr :: ~@0) 
    | (stmt :: ~@0) | (block :: ~@0) | (pa :: ~@0)
    | LB, error("unclosed '{'") | RB, error("unexpected '}'")
    | LP, error("unclosed '('") | RP, error("unexpected ')'")
    | id, LK, error("unclosed '['") | LK, error("unexpected '['") | RK, error("unexpected ']'")
    | any
    ;"""))
    
    someExpr = script.compile("(l_integer | l_string | l_regex | id | (expr :: ~@0));")
    yield "reform comma expressions", Search(script.compile("""
    (r_print, (<>expr :: @someExpr, +(comma, @someExpr)))
    | (expr :: @someExpr, LK, (<>expr :: @someExpr, +((null <- comma), @someExpr), RK))
    | (stmt :: ~@0) | (block :: ~@0) | (pa :: ~@0)
    | comma, error("unexpected comma (,)") 
    ;""", replaces={ "someExpr" : someExpr }))

class ExprInterpreter(object):
    def __init__(self):
        self.nr, self.line, self.curFields = None, None, None
        self.varTable = {}
    
    def eval_expr(self, exprNode):
        def cast_to_int(s): return 0 if not s else int(s) # an empty string is converted to 0

        if exprNode[0] != "expr":
            assert len(exprNode) == 2
            lbl, val = exprNode[0], exprNode[1]
            if lbl == "id": return self.varTable[val] # may raise KeyError
            elif lbl == "l_integer": return int(val)
            elif lbl == "l_string": return val[1:-1] # remove enclosing double quotes.
            elif lbl == "l_regex": 
                reString = val[1:-1] # remove /-chars.
                return 1 if re.match(reString, self.line) else 0
            assert False
        
        seq = exprNode[1:]
        assert seq
        if seq[0][0] in ( "op_minus", "op_plus", "op_not", "op_dollar" ): # unary
            assert len(seq) >= 2
            value = self.eval_expr(seq[-1])
            for op in reversed(seq[:-1]):
                opLbl = op[0]
                if opLbl == "op_minus": value = -cast_to_int(value)
                elif opLbl == "op_plus": value = cast_to_int(value)
                elif opLbl == "op_not": value = (1 if value in (0, '') else 0)
                elif opLbl == "op_dollar": 
                    index = cast_to_int(value)
                    if index < 0: raise IndexError
                    value = self.curFields[index] # may raise IndexError
                else:
                    assert False
            return value
        
        assert len(seq) >= 3
        seq1lbl = seq[1][0]
        if seq1lbl == "LK": # a[...]
            #assert seq[0][0] == "id"; assert seq[-1][0] == "RK"
            indexStr = "\t".join(str(self.eval_expr(v)) for v in seq[2::2])
            var = self.varTable.setdefault(seq[0][1], {})
            return var.setdefault(indexStr, "")
        
        if seq1lbl == "op_cat":
            return "".join(str(self.eval_expr(v)) for v in seq[0::2])
        
        if seq1lbl in ( "op_mul", "op_div", "op_mod", "op_minus", "op_plus" ):
            value = cast_to_int(self.eval_expr(seq[0]))
            for op, rightExpr in zip(seq[1::2], seq[2::2]):
                opLbl = op[0]
                rightValue = cast_to_int(self.eval_expr(rightExpr))
                if opLbl == "op_mul": value = value * rightValue
                elif opLbl == "op_div": value = value // rightValue
                elif opLbl == "op_mod": value = value % rightValue
                elif opLbl == "op_minus": value = value - rightValue
                elif opLbl == "op_plus": value = value + rightValue
                else:
                    assert False
            return value
        
        if seq1lbl in ( "op_gt", "op_ge", "op_lt", "op_le", "op_ne", "op_eq" ):
            assert len(seq) == 3
            leftValue = self.eval_expr(seq[0])
            opLbl = seq[1][0]
            rightValue = self.eval_expr(seq[2])
            if isinstance(leftValue, str): rightValue = str(rightValue)
            elif isinstance(rightValue, str): leftValue = str(leftValue)
            if opLbl == "op_gt": return leftValue > rightValue
            elif opLbl == "op_ge": return leftValue >= rightValue
            elif opLbl == "op_lt": return leftValue < rightValue
            elif opLbl == "op_le": return leftValue <= rightValue
            elif opLbl == "op_ne": return leftValue != rightValue
            elif opLbl == "op_eq": return leftValue == rightValue
            else:
                assert False
            return value
        
        if seq1lbl == "op_and":
            for e in seq[0::2]:
                value = self.eval_expr(e)
                if value in (0, ''): return 0
            return value
        
        if seq1lbl == "op_or":
            for e in seq[0::2]:
                value = self.eval_expr(e)
                if value not in (0, ''): return value
            return 0
        
        if seq1lbl == "op_assign":
            assingedValue = self.eval_expr(seq[-1])
            for e, op in zip(seq[0::2], seq[1::2]):
                assert op[0] == "op_assign"
                if e[0] == "id":
                    self.varTable[e[1]] = assingedValue
                elif e[0] == "expr" and len(e) >= 5 and e[2][0] == "LK":
                    #assert e[1][0] == "id"; assert e[-1][0] == "RK"
                    indexStr = "\t".join(str(self.eval_expr(v)) for v in e[3::2])
                    var = self.varTable.setdefault(e[1][1], {})
                    var[indexStr] = assingedValue
                else:
                    assert False # invalid l-value
            return assingedValue
        
        assert False # unknown operator/invalid expression

class StmtInterpreter(ExprInterpreter):
    class NextStmt(Exception): pass

    def __init__(self, ast):
        ExprInterpreter.__init__(self)
        self.beginActions = []; self.endActions = []; self.patternActions = []
        d = { "r_BEGIN" : self.beginActions, "r_END" : self.endActions }
        for paNode in ast[1:]:
            exprNode, blockNode = paNode[1], paNode[2]
            d.get(exprNode[0], self.patternActions).append(( exprNode, blockNode ))
    
    def expects_input(self): return len(self.patternActions + self.endActions) > 0
    
    def apply_begin(self):
        self.nr, self.line, self.curFields = 0, None, []
        self.varTable.update([ ( "NR", self.nr ), ( "NF", 0 ) ])
        for _, blockNode in self.beginActions: self.exec_stmt(blockNode)
            
    def apply_end(self):
        self.nr, self.line, self.curFields = -1, None, []
        self.varTable.update([ ( "NF", 0 ) ])
        for _, blockNode in self.endActions: self.exec_stmt(blockNode)
    
    def apply_line(self, nr, line):
        assert nr >= 1
        fields = line.split()
        self.nr, self.line, self.curFields = nr, line, [ line ] + fields
        self.varTable.update([ ( "NR", self.nr ), ( "NF", len(fields) ) ])
        try:
            for exprNode, blockNode in self.patternActions:
                if exprNode[0] == "expr_empty" or self.eval_expr(exprNode): 
                    self.exec_stmt(blockNode)
        except StmtInterpreter.NextStmt: 
            pass
            
    def exec_stmt(self, stmtNode):
        if stmtNode[-1][0] in ("newline", "semicolon"):
            stmtNode = stmtNode[:-1]
        if stmtNode[0] == "block_empty":
            stmtNode = [ "stmt", "r_print_empty" ]
        
        if stmtNode[0] == "block":
            for stmt in stmtNode[1:]:
                self.exec_stmt(stmt)
            return
        
        assert stmtNode[0] == "stmt"
        cmdLbl = stmtNode[1][0]
        if cmdLbl == "r_if":
            seq = stmtNode[2:]
            while seq:
                if self.eval_expr(seq[0]) not in (0, ''):
                    self.exec_stmt(seq[1])
                    break # while seq
                if len(seq) == 2: break # while seq
                if seq[2][0] == "r_else":
                    self.exec_stmt(seq[3])
                    break # while seq
                seq = seq[3:]
        elif cmdLbl == "r_while":
            while self.eval_expr(stmtNode[2]) not in (0, ''):
                self.exec_stmt(stmtNode[3])
        elif cmdLbl == "r_print":
            print " ".join(str(self.eval_expr(v)) for v in stmtNode[2::2])
        elif cmdLbl == "r_print_empty":
            print self.line
        elif cmdLbl == "r_next":
            raise StmtInterpreter.NextStmt
        elif cmdLbl == "r_null_statement":
            pass
        else:
            assert len(stmtNode) == 2
            self.eval_expr(stmtNode[1])

def main(debugTrace=False):
    import sys
    
    if len(sys.argv) == 1:
        print "usage: tinyawk -f <script> [ <input> ]\nAn interpreter of a awk-like small language."
        return
    
    assert len(sys.argv) in (3, 4)
    assert sys.argv[1] == "-f"
    scriptFile = sys.argv[2]
    inputFile = sys.argv[3] if len(sys.argv) == 4 else None
    debugWrite = sys.stderr.write if debugTrace else None
    
    f = open(scriptFile, "r")
    try:
        script = f.read()
    finally: f.close()
    script = script + "\n" # prepare for missing new-line char at the last line
    
    # parsing
    seq = split_to_str(script)
    des = []
    des.extend(tokenizing_expr_iter())
    des.extend(stmt_parsing_expr_iter()) 
    des.extend(expr_parsing_expr_iter())
    for desc, expr in des:
        if debugWrite:
            debugWrite("\n".join(treeseq.seq_pretty(seq)) + "\n") # prints a seq
            debugWrite("step: %s\n" % desc)
        try:
            newSeq = expr.parse(seq)
        except InterpretError, e: print repr(e); raise e
        if newSeq is None: raise SystemError("parse error")
        seq = newSeq
    if debugWrite: debugWrite("\n".join(treeseq.seq_pretty(seq)) + "\n") # prints a seq

    # interpretation
    interp = StmtInterpreter(seq)
    def dbgwrite(): 
        if debugWrite: debugWrite("variables=%s\n" % repr(interp.varTable))

    interp.apply_begin(); dbgwrite()
    if interp.expects_input():
        f = open(inputFile, "r") if inputFile else sys.stdin
        for lnum, L in enumerate(f):
            interp.apply_line(lnum+1, L.rstrip()); dbgwrite()
        if inputFile: f.close()
        interp.apply_end(); dbgwrite()

if __name__ == '__main__':
    main(debugTrace=True)
