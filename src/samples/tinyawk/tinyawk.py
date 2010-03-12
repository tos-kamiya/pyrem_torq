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

import re
import pyrem_torq
from pyrem_torq.expression import *
import pyrem_torq.treeseq as ptt # for debug code
compile = pyrem_torq.script.compile

def tokenize(text):
    p = "|".join([
        r"/[^/\r\n]*/", r'"[^"\r\n]*"', r"\d+", # literals (regex, string, integer)
        r"#[^\r\n]*", # comment
        r"[ \t]+", r"\r\n|\r|\n", # white spaces, newline
        r"[a-zA-Z_](\w|_)*", # identifier
        r"[<>!=]=|&&|[|][|]", r"[-+*/%<>!=()${},;]|\[|\]", # operators
        r"." # invalid chars
    ])
    return [ 'code' ] + [m.group() for m in re.finditer(p, text)]

def _build_parsing_exprs():
    descAndExprs = []
    
    # identify reserved words, literals, identifiers
    e = Search(compile(r"""
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
    | (nul <- r"^[ \t#]")
    | any, err("unexpected character")
    ;""")[0])
    descAndExprs.append(( "identify reserved words, literals, identifiers", e ))
    
    # identify statement-terminating new-line chars
    e = Search(compile(r"""
    (comma | LB | op_or | op_and | r_else), (nul <- newline)
    ;""")[0])
    descAndExprs.append(( "remove neglected new-line characters", e ))
    
    # parse pattern-actions and blocks.
    stmtLevelBlock = compile("""
    (block <- (nul <- LB), *(xcp(RB), @0), (nul <- RB)) 
    | any
    ;""")[0]
    actionLevelBlock = compile(r"""
    (pa <- 
        ((r_BEGIN | r_END) | (expr_empty <-)),
        (block <- (nul <- LB), *(xcp(RB), @stmtLevelBlock), (nul <- RB)), 
        (nul <- newline))
    | (pa <- 
        (expr <- +any^(LB | newline)), 
        ((block <- (nul <- LB), *(xcp(RB), @stmtLevelBlock), (nul <- RB)) | (block_empty <-)),
        (nul <- newline))
    | (nul <- newline)
    ;""", replaces={ 'stmtLevelBlock' : stmtLevelBlock })[0]
    e = [0,None] * actionLevelBlock
    descAndExprs.append(( "parse pattern-actions and blocks", e ))
    
    # parse statements
    getSimpleStmt = compile(r"""
    (stmt <- 
        (r_null_statement <-), semicolon 
        | (r_print_empty <- r_print), (semicolon | newline)
        | r_print, (expr <- +any^(semicolon | newline)), (semicolon | newline)
        | r_print, err("invalid print statement")
        | r_next, (semicolon | newline)
        | r_next, err("invaild 'next' statement")
        | (expr <- +any^(semicolon | newline)), (semicolon | newline))
    ;""")[0]
    e = Search(compile(r"""
    (stmt <- 
        (r_if, (nul <- LP), (expr <- +any^(newline | RP)), (nul <- RP), ?(nul <- newline), ((block :: ~@0) | @getSimpleStmt),
        *((r_elif <- r_else, r_if), (nul <- LP), (expr <- +any^(newline | RP)), (nul <- RP), ?(nul <- newline), ((block :: ~@0) | @getSimpleStmt)),
        ?(r_else, ((block :: ~@0) | @getSimpleStmt))))
    | r_if, err("invalid 'if' statement") | r_else, err("'else' doesn't have a matching 'if'") 
    | (stmt <- r_while, (nul <- LP), (expr <- +any^(newline | RP)), (nul <- RP), ((block :: ~@0) | @getSimpleStmt))
    | r_while, err("invalid 'while' statement")
    | @getSimpleStmt
    | (nul <- newline)
    | semicolon, err("unexpected semicolon (;)")
    | (block :: ~@0) 
    | (pa :: (r_BEGIN | r_END | expr_empty | expr), (block :: ~@0))
    | any, err("unexpected token")
    ;""", replaces={ 'getSimpleStmt' : getSimpleStmt })[0])
    descAndExprs.append(( "parse statements", e ))
    
    # build expression parser
    def build_expression_parser():
        n = Node
        kit = pyrem_torq.extra.operator_builer.OperatorBuilder()
        kit.atomic_term_expr = Or(n("l_integer"), n("l_string"), n("l_regex"), n("id"))
        kit.composed_term_node_labels = ( "expr", )
        kit.generated_term_label = "expr"
        
        des = []
        
        des.append(( "paren", kit.build_O_expr(( Drop(n("LP")), Drop(n("RP")) )) ))
        # Drop parentheses chars
        
        des.append(( "index", kit.build_tO_expr(( n("LK"), n("RK") )) ))
        des.append(( "unary ops", kit.build_Ot_expr(n("op_minus"), n("op_plus"), 
                n("op_not"), n("op_dollar")) ))
        des.append(( "binary mul/div", kit.build_tOt_expr(n("op_mul"), n("op_div"), n("op_mod")) ))
        des.append(( "binary add/sub", kit.build_tOt_expr(n("op_minus"), n("op_plus")) ))
        
        des.append(( "binary string concatenate", kit.build_tOt_expr(InsertNode("op_cat")) ))
        # The concatenation operator is epsilon, so that insert a token 'op_cat' where the operator appears
        
        des.append(( "binary compare ops", kit.build_tOt_expr(\
                n("op_gt"), n("op_ge"), n("op_lt"), n("op_le"), n("op_ne"), n("op_eq")) ))
        des.append(( "binary logical-and", kit.build_tOt_expr(n("op_and")) ))
        des.append(( "binary logical-or", kit.build_tOt_expr(n("op_or")) ))
        des.append(( "comma", kit.build_tOt_expr(n("comma")) ))
        des.append(( "binary assign op", kit.build_tOt_expr(n("op_assign")) ))
        return des
    for desc, eParser in build_expression_parser():
        e = Search(compile("""(expr :: @eParser)
        | (stmt :: ~@0) | (block :: ~@0) | (pa :: ~@0)
        ;""", replaces={ "eParser" : eParser })[0])
        descAndExprs.append(( "expression " + desc, e ))
    
    descAndExprs.append(( "remove redundant paren", Search(compile("""
    req(expr :: expr | l_integer | l_string | l_regex | id), (<>expr :: @0)
    | (expr :: id, LK, *(xcp(RK), @0), RK) 
    | (expr :: ~@0) 
    | (stmt :: ~@0) | (block :: ~@0) | (pa :: ~@0)
    | LB, err("unclosed '{'") | RB, err("unexpected '}'")
    | LP, err("unclosed '('") | RP, err("unexpected ')'")
    | id, LK, err("unclosed '['") | LK, err("unexpected '['") | RK, err("unexpected ']'")
    | any
    ;""")[0]) ))
    
    someExpr = compile("(l_integer | l_string | l_regex | id | (expr :: ~@0));")[0]
    descAndExprs.append(( "reform comma expressions", Search(compile("""
    (r_print, (<>expr :: @someExpr, +(comma, @someExpr)))
    | (expr :: @someExpr, LK, (<>expr :: @someExpr, +((nul <- comma), @someExpr), RK))
    | (stmt :: ~@0) | (block :: ~@0) | (pa :: ~@0)
    | comma, err("unexpected comma (,)") 
    ;""", replaces={ "someExpr" : someExpr })[0]) ))
    
    return descAndExprs

parsing_exprs = _build_parsing_exprs()

class Interpreter(object):
    class NextStmt(Exception): pass

    def __init__(self, ast):
        self.patternActions = [( paNode[1], paNode[2] ) for paNode in ast[1:]]
        self.nr, self.line, self.curFields = None, None, None
        self.varTable = {}
    
    def do_begin(self): 
        self.nr, self.line, self.curFields = 0, None, []
        self.varTable.update([ ( "NR", self.nr ), ( "NF", 0 ) ])
        try:
            self._exec()
        except Interpreter.NextStmt:
            raise SystemError("next statement in BEGIN action")
            
    def do_end(self):
        self.nr, self.line, self.curFields = -1, None, []
        self.varTable.update([ ( "NF", 0 ) ])
        self._exec()
    
    def do_line(self, nr, line):
        assert nr >= 1
        fields = line.split()
        self.nr, self.line, self.curFields = nr, line, [ line ] + fields
        self.varTable.update([ ( "NR", self.nr ), ( "NF", len(fields) ) ])
        self._exec()

    def _exec(self):
        for exprNode, blockNode in self.patternActions:
            e0 = exprNode[0]
            if e0 == "r_BEGIN":
                if self.nr == 0: self.exec_stmt(blockNode)
            elif e0 == "r_END":
                if self.nr == -1: self.exec_stmt(blockNode)
            else:
                try:
                    if self.nr >= 1 and (e0 == "expr_empty" or self.eval_expr(exprNode)): 
                        self.exec_stmt(blockNode)
                except Interpreter.NextStmt:
                    break # for 
     
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
            raise Interpreter.NextStmt
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
    seq = tokenize(script)
    for desc, expr in parsing_exprs:
        if debugWrite:
            debugWrite("\n".join(ptt.seq_pretty(seq)) + "\n") # prints a seq
            debugWrite("step: %s\n" % desc)
        try:
            newSeq = expr.parse(seq)
        except InterpretError, e: print repr(e); raise e
        if newSeq is None: raise SystemError("parse error")
        seq = newSeq
    if debugWrite: debugWrite("\n".join(ptt.seq_pretty(seq)) + "\n") # prints a seq

    # interpretation
    interp = Interpreter(seq)
    def dbgwrite(): 
        if debugWrite: debugWrite("variables=%s\n" % repr(interp.varTable))

    interp.do_begin(); dbgwrite()
    f = open(inputFile, "r") if inputFile else sys.stdin
    for lnum, L in enumerate(f):
        interp.do_line(lnum+1, L.rstrip()); dbgwrite()
    if inputFile: f.close()
    interp.do_end(); dbgwrite()

if __name__ == '__main__':
    main(debugTrace=True)
