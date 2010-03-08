import re
from pyrem_torq.compile import compile
from pyrem_torq.expression import *
import pyrem_torq.treeseq as ptt
from pyrem_torq.extra.operator_builer import OperatorBuilder

def tokenize(text):
    p = "|".join([
        r"/[^/\n]*/", # regular expression
        r'"[^"\n]*"', # string literal
        r"#[^\n]*", # comment
        r"[ \t]+", r"\n", # white spaces, newline
        r"[a-zA-Z_](\w|_)+", # identifier
        r"\d+", # integer literal
        r"[<>!=]=|!?~|&&|[|][|]", r"[-+*/%=!()${},;]|\[|\]" # operators
    ])
    return [ 'code' ] + [m.group() for m in re.finditer(p, text)]

def _build_parsing_exprs():
    descAndExprs = []
    
    # identify reserved words, literals, identifiers
    e = Search(compile(r"""
    (r_BEGIN <- "BEGIN") | (r_END <- "END")
    | (r_print <- "print")
    | (r_if <- "if") | (r_else <- "else") 
    | (id <- r"^[a-zA-Z_]") 
    | (l_integer <- r"^[0-9]") | (l_string <- r"^\"") | (l_regex <- r"^/")
    | (op_gt <- "<") | (op_ge <- "<=") | (op_lt <- "<") | (op_le <- "<=") | (op_ne <- "!=") | (op_eq <- "==")
    | (op_match <- "~") | (op_notmatch <- "!~")
    | (op_and <- "&&") | (op_or <- "||")
    | (op_plus <- "+") | (op_minus <- "-") | (op_mul <- "*") | (op_div <- "/") | (op_mod <- "%")
    | (op_assign <- "=") | (op_not <- "!") | (op_dollar <- "$")
    | (LP <- "(") | (RP <- ")") | (LB <- "{") | (RB <- "}") | (LK <- "[") | (RK <- "]")
    | (comma <- ",") | (semicolon <- ";")
    | (null <- r"^[ \t]")
    ;""")[0])
    descAndExprs.append(( "identify reserved words, literals, identifiers", e ))
    
    # remove neglected new-line characters
    e = Search(compile(r"""
    (comma | LB | op_or | op_and | r_else), (null <- +"\n")
    | (newline <- "\n")
    ;""")[0])
    descAndExprs.append(( "remove neglected new-line characters", e ))
    
    # parse pattern-actions and blocks.
    stmtLevelBlock = compile(r"""
    (block <- (null <- LB), *(xcp(RB), @0), (null <- RB))
    | any
    ;""")[0]
    actionLevelBlock = compile(r"""
    (pa <- 
        ((r_BEGIN | r_END) | (expr_empty <-)),
        (block <- (null <- LB), *(xcp(RB), @stmtLevelBlock), (null <- RB)), 
        (null <- newline)
    )
    | (pa <- 
        (expr <- +any^(LB | newline)), 
        ((block <- (null <- LB), *(xcp(RP), @stmtLevelBlock), (null <- RB)) | (block_empty <-)),
        (null <- newline)
    )
    | (null <- newline)
    ;""", replaces={ 'stmtLevelBlock' : stmtLevelBlock })[0]
    e = [0,None] * actionLevelBlock
    descAndExprs.append(( "parse pattern-actions and blocks", e ))
    
    # parse statements
    getSimpleStmt = compile(r"""
    (stmt <- 
        semicolon 
        | (expr <- +any^(semicolon | newline)), (null <- (semicolon | newline))
    )
    ;""")[0]
    e = Search(compile(r"""
    (stmt <- 
        (r_if, (null <- LP), (expr <- +any^(newline | RP)), (null <- RP), ((block :: ~@0) | @getSimpleStmt),
        *((r_elif <- r_else, r_if), (null <- LP), (expr <- +any^(newline | RP)), (null <- RP), ((block :: ~@0) | @getSimpleStmt)),
        ?(r_else, ((block :: ~@0) | @getSimpleStmt)))
    )
    | (stmt <- r_print, (expr <- +any^(semicolon | newline)), (null <- (semicolon | newline)))
    | @getSimpleStmt
    | (null <- newline)
    | (block :: ~@0) 
    | (pa :: (r_BEGIN | r_END | expr | expr_empty), (block :: ~@0))
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
        | (stmt :: ~@0)
        | (block :: ~@0)
        | (pa :: ((expr :: ~@eParser) | expr_empty), (block :: ~@0))
        ;""", replaces={ "eParser" : eParser })[0])
        descAndExprs.append(( desc, e ))
    
    someExpr = compile("(l_integer | l_string | l_regex | id | (expr :: ~@0));")[0]
    descAndExprs.append(( "reform comma expressions", Search(compile("""
    (r_print, (<>expr :: @someExpr, +(comma, @someExpr)))
    | (expr :: @someExpr, LK, (<>expr :: @someExpr, +((null <- comma), @someExpr), RK))
    | (stmt :: ~@0) | (block :: ~@0) | (pa :: ~@0)
    ;""", replaces={ "someExpr" : someExpr })[0]) ))
    
    descAndExprs.append(( "remove redundant paren", Search(compile("""
    req(expr :: expr), (<>expr :: @0)
    | (expr :: ~@0) | (stmt :: ~@0) | (block :: ~@0) | (pa :: ~@0)
    ;""")[0]) ))
    
    return descAndExprs

parsing_exprs = _build_parsing_exprs()

class PatternActionInterpreter(object):
    def __init__(self):
        self.nr = None
        self.nf = None
        self.line = None
        self.curFields = None
        self.variableTable = {}
        
    def __call__(self, exprNode, blockNode, nr, line):
        if nr in ( 0, -1 ):
            if not(nr == 0 and exprNode[0] == "r_BEGIN" or \
                    nr == -1 and exprNode[0] == "r_END"): return
            self.line, self.curFields = "", []
            self.variableTable["NF"] = self.nf = 0
            if nr == 0:
                self.variableTable["NR"] = self.nr = 0
            #else: pass # don't touch variable NR
            self.interp_stmt(blockNode)
        else:
            if exprNode[0] in ( "r_BEGIN", "r_END" ): return
            self.line = line
            fields = line.split()
            self.variableTable["NF"] = self.nf = len(fields)
            self.curFields = [ line ] + fields
            self.variableTable["NR"] = self.nr = nr
            if self.interp_expr(exprNode):
                self.interp_stmt(blockNode)
     
    def interp_expr(self, exprNode):
        lbl = exprNode[0]
        if lbl != "expr":
            if lbl == "expr_empty": 
                return 1
            elif lbl == "id": 
                return self.variableTable[exprNode[1]] # may raise KeyError
            elif lbl == "l_integer": 
                return int(exprNode[1])
            elif lbl == "l_string": 
                return exprNode[1][1:-1] # remove enclosing double quotes.
            elif lbl == "l_regex": 
                reString = exprNode[1][1:-1] # remove enclosing slashes.
                return 1 if re.match(reString, self.line) else 0
            assert False
        
        seq = exprNode[1:]
        assert seq
        if seq[0][0] in ( "op_minus", "op_plus", "op_not", "op_dollar" ): # unary
            assert len(seq) >= 2
            value = self.interp_expr(seq[-1]); seq = seq[:-1]
            while seq:
                seq_1lbl = seq[-1][0]
                if seq_1lbl == "op_minus": value = value * -1
                elif seq_1lbl == "op_plus": value = value
                elif seq_1lbl == "op_not": value = 1 if value == 0 else 0
                elif seq_1lbl == "op_dollar": value = self.curFields[int(value)]
                else:
                    assert False
                seq = seq[:-1]
            return value
        
        assert len(seq) >= 3
        seq1lbl = seq[1][0]
        if seq1lbl == "LK": # a[...]
            assert seq[0][0] == "id"
            assert seq[-1][0] == "RK"
            indexStr = "\t".join(str(self.interp_expr(v)) for v in seq[2::2])
            var = self.variableTable.setdefault(seq[1][1], {})
            return var.setdefault(indexStr, "")
        
        if seq1lbl == "op_cat":
            return "".join(str(self.interp_expr(v)) for v in seq[0::2])
        
        if seq1lbl in ( "op_mul", "op_div", "op_mod" ):
            value = int(self.interp_expr(seq[0]))
            for op, rightExpr in zip(seq[1::2], seq[2::2]):
                opLbl = op[0]
                rightValue = int(self.interp_expr(rightExpr))
                if opLbl == "op_mul": value = value * rightValue
                elif opLbl == "op_div": value = value // rightValue
                elif opLbl == "op_mod": value = value % rightValue
                else:
                    assert False
            return value
        
        if seq1lbl in ( "op_minus", "op_plus" ):
            value = int(self.interp_expr(seq[0]))
            for op, rightExpr in zip(seq[1::2], seq[2::2]):
                opLbl = op[0]
                rightValue = int(self.interp_expr(rightExpr))
                if opLbl == "op_minus": value = value - rightValue
                elif opLbl == "op_plus": value = value + rightValue
                else:
                    assert False
            return value
        
        if seq1lbl in ( "op_gt", "op_ge", "op_lt", "op_le", "op_ne", "op_eq" ):
            assert len(seq) == 3
            leftValue = self.interp_expr(seq[0])
            opLbl = seq[1][0]
            rightValue = self.interp_expr(seq[2])
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
            leftValue = str(self.interp_expr(seq[0]))
            opLbl = seq[1][0]
            assert seq[2][0] == "l_regex"
            reString = seq[2][1][1:-1] # remove /-chars.
            return 1 if re.match(reString, leftValue) else 0
        
        if seq1lbl == "op_and":
            for e in seq[0::2]:
                if not self.interp_expr(e): return 0
            return 1
        
        if seq1lbl == "op_or":
            for e in seq[0::2]:
                if self.interp_expr(e): return 1
            return 0
        
        if seq1lbl == "op_assign":
            assingedValue = self.interp_expr(seq[-1])
            for e, op in zip(seq[0::2], seq[1::2]):
                assert op[0] == "op_assign"
                if e[0] == "id":
                    self.variableTable[e[1]] = assingedValue
                elif e[0] == "expr" and len(e) >= 5 and e[2][0] == "LK":
                    assert e[1][0] == "id"
                    assert e[-1][0] == "RK"
                    indexStr = "\t".join(str(self.interp_expr(v)) for v in e[3::2])
                    var = self.variableTable.setdefault(e[1][1], {})
                    var[indexStr] = assingedValue
                else:
                    assert False # invalid l-value
            return assingedValue
        
        if seq1lbl == "comma":
            assert False # a comma appears outside of [] or a print statement
        
        assert False # unknown operator/invalid expression
            
    def interp_stmt(self, stmtNode):
        if stmtNode and stmtNode[-1][0] in ("newline", "semicolon"):
            stmtNode = stmtNode[:-1]
        
        assert len(stmtNode) >= 2
        if stmtNode[0] == "block":
            for stmt in stmtNode[1:]:
                self.interp_stmt(stmt)
            return
        
        assert stmtNode[0] == "stmt"
        if stmtNode[1][0] == "r_if":
            seq = stmtNode[1:]
            while seq:
                assert len(seq) >= 3
                assert seq[0] in ( "r_if", "r_elif" )
                if self.interp_expr(seq[1]):
                    self.interp_stmt(seq[2])
                    break # while seq
                assert len(seq) >= 5
                if seq[3] == "r_else":
                    self.interp_stmt(seq[4])
                    break # while seq
                assert seq[3] == "r_elif"
                seq = seq[3:]
            return
        
        if stmtNode[1][0] == "r_print":
            if len(stmtNode) == 2:
                print self.line
            else:
                print " ".join(str(self.interp_expr(v)) for v in stmtNode[2::2])
            return
        
        assert len(stmtNode) == 2
        self.interp_expr(stmtNode[1])

def main(debugTrace=False):
    import sys
    
    if len(sys.argv) == 1:
        print("""
usage: tinyawk <script> <input>...
  A tiny-awk interpreter.
"""[1:-1])
        sys.exit(0)
    
    scriptFile = sys.argv[1]
    inputFiles = sys.argv[2:]
    debugWrite = sys.stderr.write if debugTrace else None
    
    with open(scriptFile, "r") as f:
        script = f.read()
    
    # parsing
    seq = tokenize(script)
    for desc, expr in parsing_exprs:
        if debugWrite:
            debugWrite("\n".join(ptt.seq_pretty(seq)) + "\n") # prints an seq
            debugWrite("step: %s\n" % desc)
        newSeq = expr.parse(seq)
        if newSeq is None: raise SystemError
        seq = newSeq
    if debugWrite: debugWrite("\n".join(ptt.seq_pretty(seq)) + "\n") # prints an seq

    def pa_iter():
        for paNode in seq[1:]:
            assert len(paNode) == 3
            exprNode, blockNode = paNode[1], paNode[2]
            yield exprNode, blockNode
        
    # interpretation
    interp = PatternActionInterpreter()
    for exprNode, blockNode in pa_iter():
        interp(exprNode, blockNode, 0, None)
    if debugWrite: debugWrite("variables=%s\n" % repr(interp.variableTable))
    nr = 0
    for inputFile in inputFiles:
        with open(inputFile, "r") as f:
            inputLines = f.readlines()
        inputLines = [L.rstrip() for L in inputLines]
        for L in inputLines:
            nr += 1
            for exprNode, blockNode in pa_iter():
                interp(exprNode, blockNode, nr, L)
            if debugWrite: debugWrite("variables=%s\n" % repr(interp.variableTable))
    for exprNode, blockNode in pa_iter():
        interp(exprNode, blockNode, -1, None)
    if debugWrite: debugWrite("variables=%s\n" % repr(interp.variableTable))

if __name__ == '__main__':
    main(debugTrace=True)
