# tinyawk
# an interpreter of a very small subset of AWK programming language.
# supported reserved words are:
#   BEGIN END NF NR if else print while
#   ( ) [ ] { } ; , < <= > >= == != ~ !~ && || ! - + * / % $
# note that: 
# (1) escape sequences are not supported in either string literal or regex.
# (2) all numbers are integers, no floating points.
# (3) assignment to NF, NR or $* is undefined behavior.

import re
from pyrem_torq.compile import compile
from pyrem_torq.expression import *
import pyrem_torq.treeseq as ptt
from pyrem_torq.extra.operator_builer import OperatorBuilder

def tokenize(text):
    p = "|".join([
        r"/[^/\n]*/", r'"[^"\n]*"', r"\d+", # literals (regex, string, integer)
        r"#[^\n]*", # comment
        r"[ \t]+", r"\n", # white spaces, newline
        r"[a-zA-Z_](\w|_)*", # identifier
        r"[<>!=]=|!?~|&&|[|][|]", r"[-+*/%<>!=()${},;]|\[|\]" # operators
    ])
    return [ 'code' ] + [m.group() for m in re.finditer(p, text)]

def _build_parsing_exprs():
    descAndExprs = []
    
    # identify reserved words, literals, identifiers
    e = Search(compile(r"""
    (r_BEGIN <- "BEGIN") | (r_END <- "END")
    | (r_print <- "print") | (r_if <- "if") | (r_else <- "else") | (r_while <- "while")
    | (id <- r"^[a-zA-Z_]") 
    | (l_integer <- r"^[0-9]") | (l_string <- r"^\"") | (l_regex <- r"^/")
    | (op_gt <- ">") | (op_ge <- ">=") | (op_lt <- "<") | (op_le <- "<=") | (op_ne <- "!=") | (op_eq <- "==")
    | (op_match <- "~") | (op_notmatch <- "!~")
    | (op_and <- "&&") | (op_or <- "||")
    | (op_plus <- "+") | (op_minus <- "-") | (op_mul <- "*") | (op_div <- "/") | (op_mod <- "%")
    | (op_assign <- "=") | (op_not <- "!") | (op_dollar <- "$")
    | (LP <- "(") | (RP <- ")") | (LB <- "{") | (RB <- "}") | (LK <- "[") | (RK <- "]")
    | (comma <- ",") | (semicolon <- ";")
    | (null <- r"^[ \t#]")
    ;""")[0])
    descAndExprs.append(( "identify reserved words, literals, identifiers", e ))
    
    # identify statement-terminating new-line chars
    e = Search(compile(r"""
    (comma | LB | op_or | op_and | r_else), (null <- +"\n")
    | (newline <- "\n")
    ;""")[0])
    descAndExprs.append(( "remove neglected new-line characters", e ))
    
    # parse pattern-actions and blocks.
    stmtLevelBlock = compile("(block <- (null <- LB), *(xcp(RB), @0), (null <- RB)) | any;")[0]
    actionLevelBlock = compile(r"""
    (pa <- 
        ((r_BEGIN | r_END) | (expr_empty <-)),
        (block <- (null <- LB), *(xcp(RB), @stmtLevelBlock), (null <- RB)), 
        (null <- newline))
    | (pa <- 
        (expr <- +any^(LB | newline)), 
        ((block <- (null <- LB), *(xcp(RP), @stmtLevelBlock), (null <- RB)) | (block_empty <-)),
        (null <- newline))
    | (null <- newline)
    ;""", replaces={ 'stmtLevelBlock' : stmtLevelBlock })[0]
    e = [0,None] * actionLevelBlock
    descAndExprs.append(( "parse pattern-actions and blocks", e ))
    
    # parse statements
    getSimpleStmt = compile(r"""
    (stmt <- 
        semicolon 
        | r_print, (expr <- +any^(semicolon | newline)), (semicolon | newline)
        | (expr <- +any^(semicolon | newline)), (semicolon | newline))
    ;""")[0]
    e = Search(compile(r"""
    (stmt <- 
        (r_if, (null <- LP), (expr <- +any^(newline | RP)), (null <- RP), ?(null <- newline), ((block :: ~@0) | @getSimpleStmt),
        *((r_elif <- r_else, r_if), (null <- LP), (expr <- +any^(newline | RP)), (null <- RP), ?(null <- newline), ((block :: ~@0) | @getSimpleStmt)),
        ?(r_else, ((block :: ~@0) | @getSimpleStmt))))
    | (stmt <- r_while, (null <- LP), (expr <- +any^(newline | RP)), (null <- RP), ((block :: ~@0) | @getSimpleStmt))
    | @getSimpleStmt
    | (null <- newline)
    | (block :: ~@0) 
    | (pa :: (r_BEGIN | r_END | expr_empty | expr), (block :: ~@0))
    ;""", replaces={ 'getSimpleStmt' : getSimpleStmt })[0])
    descAndExprs.append(( "parse statements", e ))
    
    # build expression parser
    def build_expression_parser():
        n = Node
        kit = OperatorBuilder()
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
                n("op_gt"), n("op_ge"), n("op_lt"), n("op_le"), n("op_ne"), n("op_eq"),
                n("op_match"), n("op_notmatch")) ))
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
    | (expr :: ~@0) | (stmt :: ~@0) | (block :: ~@0) | (pa :: ~@0)
    | any
    ;""")[0]) ))
    
    someExpr = compile("(l_integer | l_string | l_regex | id | (expr :: ~@0));")[0]
    descAndExprs.append(( "reform comma expressions", Search(compile("""
    (r_print, (<>expr :: @someExpr, +(comma, @someExpr)))
    | (expr :: @someExpr, LK, (<>expr :: @someExpr, +((null <- comma), @someExpr), RK))
    | (stmt :: ~@0) | (block :: ~@0) | (pa :: ~@0)
    ;""", replaces={ "someExpr" : someExpr })[0]) ))
    
    return descAndExprs

parsing_exprs = _build_parsing_exprs()

class PatternActionInterpreter(object):
    def __init__(self):
        self.nr = None
        self.line, self.curFields = None, None
        self.varTable = {}
        
    def set_line(self, nr, line):
        self.nr = nr
        if nr in ( 0, -1 ):
            self.line, self.curFields = "", []
            self.varTable["NF"] = 0
        else:
            self.line = line
            fields = line.split()
            self.varTable["NF"] = len(fields)
            self.curFields = [ line ] + fields
        if self.nr != -1:
            self.varTable["NR"] = self.nr

    def exec_pattern_action(self, exprNode, blockNode):
        e0 = exprNode[0]
        if self.nr == 0:
            if e0 == "r_BEGIN": self.exec_stmt(blockNode)
        elif self.nr == -1:
            if e0 == "r_END": self.exec_stmt(blockNode)
        else:
            if e0 not in ("r_BEGIN", "r_END"):
                if exprNode[0] == "expr_empty" or self.eval_expr(exprNode):
                    self.exec_stmt(blockNode)
     
    def eval_expr(self, exprNode):
        def to_int(s):
            if not s: return 0
            return int(s)

        if exprNode[0] != "expr":
            assert len(exprNode) == 2
            lbl, val = exprNode[0], exprNode[1]
            if lbl == "id": 
                return self.varTable[val] # may raise KeyError
            elif lbl == "l_integer": 
                return int(val)
            elif lbl == "l_string": 
                return val[1:-1] # remove enclosing double quotes.
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
                if opLbl == "op_minus": value = to_int(value) * -1
                elif opLbl == "op_plus": value = to_int(value) * 1
                elif opLbl == "op_not": value = (1 if value in (0, '') else 0)
                elif opLbl == "op_dollar": 
                    index = to_int(value)
                    if index < 0: raise IndexError
                    value = self.curFields[index] # may raise IndexError
                else:
                    assert False
            return value
        
        assert len(seq) >= 3
        seq1lbl = seq[1][0]
        if seq1lbl == "LK": # a[...]
            assert seq[0][0] == "id"
            assert seq[-1][0] == "RK"
            assert len(filter(lambda n: n[0] == "LK", seq)) == 1
            indexStr = "\t".join(str(self.eval_expr(v)) for v in seq[2::2])
            var = self.varTable.setdefault(seq[0][1], {})
            return var.setdefault(indexStr, "")
        
        if seq1lbl == "op_cat":
            return "".join(str(self.eval_expr(v)) for v in seq[0::2])
        
        if seq1lbl in ( "op_mul", "op_div", "op_mod", "op_minus", "op_plus" ):
            value = to_int(self.eval_expr(seq[0]))
            for op, rightExpr in zip(seq[1::2], seq[2::2]):
                opLbl = op[0]
                rightValue = to_int(self.eval_expr(rightExpr))
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
        
        if seq1lbl in ( "op_match", "op_notmatch" ):
            assert len(seq) == 3
            leftValue = str(self.eval_expr(seq[0]))
            assert seq[2][0] == "l_regex"
            reString = seq[2][1][1:-1] # remove /-chars.
            value = 1 if re.match(reString, leftValue) else 0
            if seq1lbl == "op_notmatch": value = 1 - value
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
                    assert e[1][0] == "id"
                    assert e[-1][0] == "RK"
                    assert len(filter(lambda n: n[0] == "LK", e)) == 1
                    indexStr = "\t".join(str(self.eval_expr(v)) for v in e[3::2])
                    var = self.varTable.setdefault(e[1][1], {})
                    var[indexStr] = assingedValue
                else:
                    assert False # invalid l-value
            return assingedValue
        
        if seq1lbl == "comma":
            assert False # a comma appears outside of [] or a print statement
        
        assert False # unknown operator/invalid expression
            
    def exec_stmt(self, stmtNode):
        if stmtNode and stmtNode[-1][0] in ("newline", "semicolon"):
            stmtNode = stmtNode[:-1]
        
        if len(stmtNode) == 1: return
        
        if stmtNode[0] == "block_empty":
            print self.line
            return
        
        assert len(stmtNode) >= 2
        if stmtNode[0] == "block":
            for stmt in stmtNode[1:]:
                self.exec_stmt(stmt)
            return
        
        assert stmtNode[0] == "stmt"
        if stmtNode[1][0] == "r_if":
            seq = stmtNode[1:]
            while seq:
                assert len(seq) >= 3
                assert seq[0][0] in ( "r_if", "r_elif" )
                if self.eval_expr(seq[1]) not in (0, ''):
                    self.exec_stmt(seq[2])
                    break # while seq
                if len(seq) == 3: break # while seq
                if seq[3][0] == "r_else":
                    self.exec_stmt(seq[4])
                    break # while seq
                seq = seq[3:]
            return
        
        if stmtNode[1][0] == "r_while":
            assert len(stmtNode) == 4
            while self.eval_expr(stmtNode[2]) not in (0, ''):
                self.exec_stmt(stmtNode[3])
            return
        
        if stmtNode[1][0] == "r_print":
            print self.line if len(stmtNode) == 2 else \
                " ".join(str(self.eval_expr(v)) for v in stmtNode[2::2])
            return
        
        assert len(stmtNode) == 2
        self.eval_expr(stmtNode[1])

def main(debugTrace=False):
    import sys
    
    if len(sys.argv) == 1:
        print "usage: tinyawk -f <script> [ <input> ]\nAn interpreter of a awk-like small language."
        sys.exit(0)
    
    assert len(sys.argv) in (3, 4)
    assert sys.argv[1] == "-f"
    scriptFile = sys.argv[2]
    inputFile = sys.argv[3] if len(sys.argv) == 4 else None
    debugWrite = sys.stderr.write if debugTrace else None
    
    with open(scriptFile, "r") as f: script = f.read()
    script = script + "\n" # prepare for missing new-line char at the last line
    
    # parsing
    seq = tokenize(script)
    for desc, expr in parsing_exprs:
        if debugWrite:
            debugWrite("\n".join(ptt.seq_pretty(seq)) + "\n") # prints a seq
            debugWrite("step: %s\n" % desc)
        newSeq = expr.parse(seq)
        if newSeq is None: raise SystemError
        seq = newSeq
    if debugWrite: debugWrite("\n".join(ptt.seq_pretty(seq)) + "\n") # prints a seq

    # interpretation
    patternActions = [( paNode[1], paNode[2] ) for paNode in seq[1:]]
    interp = PatternActionInterpreter()
    interp.set_line(0, None)
    for exprNode, blockNode in patternActions:
        interp.exec_pattern_action(exprNode, blockNode)
    if debugWrite: debugWrite("variables=%s\n" % repr(interp.varTable))
    
    if any(e[0] not in ("r_BEGIN", "r_END") for e, b in patternActions):
        f = open(inputFile, "r") if inputFile else sys.stdin
        for lnum, L in enumerate(f):
            interp.set_line(lnum+1, L.rstrip())
            for exprNode, blockNode in patternActions:
                interp.exec_pattern_action(exprNode, blockNode)
            if debugWrite: debugWrite("variables=%s\n" % repr(interp.varTable))
        if inputFile: f.close()
    
    interp.set_line(-1, None)
    for exprNode, blockNode in patternActions:
        interp.exec_pattern_action(exprNode, blockNode)
    if debugWrite: debugWrite("variables=%s\n" % repr(interp.varTable))

if __name__ == '__main__':
    main(debugTrace=True)
