import sys, os, re
import unittest
from collections import deque

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from pyrem_torq.treeseq import seq_pretty, seq_remove_strattrs
from pyrem_torq.expression import *
from pyrem_torq.utility import split_to_strings
from pyrem_torq.extra import OperatorBuilder

def scan_seq(s):
    pat = re.compile("|".join([ r"\[", r"\]", r",", r"(\\.|[^\[\],])+" ]))
    tokens = filter(lambda token: token != ",", [m.group() for m in pat.finditer(s)])
    q = deque(tokens)
    def make_list():
        L = []
        while q:
            ti = q.popleft()
            if ti == "]":
                return L
            if ti == "[":
                innerList = make_list()
                L.append(innerList)
            else:
                L.append(ti.replace("\\", ""))
        assert False
    ti = q.popleft(); assert ti == "["
    L = make_list()
    assert not q
    return L

class TestTorqOperatorBuilder(unittest.TestCase):
    def testParseExpression(self):
        kit = OperatorBuilder()
        kit.atomic_term_expr = Rex(r"^\d") | Rex(r"^\w")
        kit.composed_term_node_labels = ( "t", )
        kit.generated_term_label = "t"
        
        descAndExprs = []
        descAndExprs.append(( "atomicExpr", kit.build_atom_to_term_expr() ))
        descAndExprs.append(( "funcCallExpr", kit.build_tO_expr(( BuildToNode("CL", Literal("(")), BuildToNode("CR", Literal(")")) ), pseudoPrefix="TO") ))
        descAndExprs.append(( "parenExpr", kit.build_O_expr(( BuildToNode("PL", Literal("(")), BuildToNode("PR", Literal(")")) )) ))
        descAndExprs.append(( "indexExpr", kit.build_tO_expr(( Literal("["), Literal("]") )) ))
        descAndExprs.append(( "unaryMinusExpr", kit.build_Ot_expr(Literal("-")) ))
        descAndExprs.append(( "binaryStarExpr", kit.build_tOt_expr(Literal("*")) ))
        descAndExprs.append(( "binaryMinusExpr", kit.build_tOt_expr(Literal("-")) ))
        descAndExprs.append(( "conditionExpr", kit.build_tOt_expr(( Literal("?"), Literal(":") ), pseudoPrefix="TOT") ))
         
        results = map(scan_seq, [
            r"[code,-,[t,1],-,[t,2],*,(,[t,3],-,[t,4],),-,[t,a],\[,[t,5],\],*,[t,6],?,[t,7],:,[t,8],-,[t,9],?,[t,b],(,[t,c],-,[t,1],\,,[t,d],),:,[t,e]]",
            r"[code,-,[t,1],-,[t,2],*,(,[t,3],-,[t,4],),-,[t,a],\[,[t,5],\],*,[t,6],?,[t,7],:,[t,8],-,[t,9],?,[t,[TO],[t,b],[CL,(],[t,c],-,[t,1],\,,[t,d],[CR,)]],:,[t,e]]",
            r"[code,-,[t,1],-,[t,2],*,[t,[PL,(],[t,3],-,[t,4],[PR,)]],-,[t,a],\[,[t,5],\],*,[t,6],?,[t,7],:,[t,8],-,[t,9],?,[t,[TO],[t,b],[CL,(],[t,c],-,[t,1],\,,[t,d],[CR,)]],:,[t,e]]",
            r"[code,-,[t,1],-,[t,2],*,[t,[PL,(],[t,3],-,[t,4],[PR,)]],-,[t,[t,a],\[,[t,5],\]],*,[t,6],?,[t,7],:,[t,8],-,[t,9],?,[t,[TO],[t,b],[CL,(],[t,c],-,[t,1],\,,[t,d],[CR,)]],:,[t,e]]",
            r"[code,[t,-,[t,1]],-,[t,2],*,[t,[PL,(],[t,3],-,[t,4],[PR,)]],-,[t,[t,a],\[,[t,5],\]],*,[t,6],?,[t,7],:,[t,8],-,[t,9],?,[t,[TO],[t,b],[CL,(],[t,c],-,[t,1],\,,[t,d],[CR,)]],:,[t,e]]",
            r"[code,[t,-,[t,1]],-,[t,[t,2],*,[t,[PL,(],[t,3],-,[t,4],[PR,)]]],-,[t,[t,[t,a],\[,[t,5],\]],*,[t,6]],?,[t,7],:,[t,8],-,[t,9],?,[t,[TO],[t,b],[CL,(],[t,c],-,[t,1],\,,[t,d],[CR,)]],:,[t,e]]",
            r"[code,[t,[t,-,[t,1]],-,[t,[t,2],*,[t,[PL,(],[t,[t,3],-,[t,4]],[PR,)]]],-,[t,[t,[t,a],\[,[t,5],\]],*,[t,6]]],?,[t,7],:,[t,[t,8],-,[t,9]],?,[t,[TO],[t,b],[CL,(],[t,[t,c],-,[t,1]],\,,[t,d],[CR,)]],:,[t,e]]",
            r"[code,[t,[TOT],[t,[t,-,[t,1]],-,[t,[t,2],*,[t,[PL,(],[t,[t,3],-,[t,4]],[PR,)]]],-,[t,[t,[t,a],\[,[t,5],\]],*,[t,6]]],?,[t,7],:,[t,[t,8],-,[t,9]],?,[t,[TO],[t,b],[CL,(],[t,[t,c],-,[t,1]],\,,[t,d],[CR,)]],:,[t,e]]]",
         ])
         
        text = "-1-2*(3-4)-a[5]*6?7:8-9?b(c-1,d):e"
        seq = [ 'code' ] + split_to_strings(text, re.compile(r"[a-z]+|(\d|[.])+|[-+*/%()?:,]|\[|\]"))
        for ( desc, expr ), result in zip(descAndExprs, results):
            print "step: %s" % desc
            seq = expr.parse(seq)
            seq_wo_attr = seq_remove_strattrs(seq)
            sys.stdout.write("\n".join(seq_pretty(seq_wo_attr)) + "\n")
            self.assertEquals(seq_wo_attr, result)
    
    def testParseExpressionWithGerbageToken(self):
        kit = OperatorBuilder()
        kit.atomic_term_expr = Rex(r"^\d")
        kit.composed_term_node_labels = ( "t", )
        kit.generated_term_label = "t"
        
        descAndExprs = []
        descAndExprs.append(( "atomicExpr", kit.build_atom_to_term_expr() ))
        descAndExprs.append(( "funcCallExpr", kit.build_tO_expr(( BuildToNode("CL", Literal("(")), BuildToNode("CR", Literal(")")) ), pseudoPrefix="TO") ))
        descAndExprs.append(( "parenExpr", kit.build_O_expr(( BuildToNode("PL", Literal("(")), BuildToNode("PR", Literal(")")) )) ))
        descAndExprs.append(( "unaryMinusExpr", kit.build_Ot_expr(Literal("-")) ))
        descAndExprs.append(( "binaryStarExpr", kit.build_tOt_expr(Literal("*")) ))
        descAndExprs.append(( "binaryMinusExpr", kit.build_tOt_expr(Literal("-")) ))
    
        text = "-1-2*(3-gerbage)-4"
        seq = [ 'code' ] + split_to_strings(text, re.compile(r"[a-z]+|(\d|[.])+|[-+*/%()?:,]|\[|\]"))
        for desc, expr in descAndExprs:
            #print "step: %s" % desc
            seq = expr.parse(seq)
            seq_wo_attr = seq_remove_strattrs(seq)
            #sys.stdout.write("\n".join(seq_pretty(seq_wo_attr)) + "\n")

    def testParseExpressionInStatement(self):
        kit = OperatorBuilder()
        kit.atomic_term_expr = Rex(r"^\d")
        kit.composed_term_node_labels = ( "t", )
        kit.generated_term_label = "t"

        descAndExprs = []
        descAndExprs.append(( "atomic", kit.build_atom_to_term_expr() ))
        descAndExprs.append(( "paren", kit.build_O_expr(( Literal("("), Literal(")") )) ))
        descAndExprs.append(( "sign", kit.build_Ot_expr(Literal("+"), Literal("-")) ))
        descAndExprs.append(( "mul,div", kit.build_tOt_expr(Literal("*"), Literal("/")) ))
        descAndExprs.append(( "add,sub", kit.build_tOt_expr(Literal("+"), Literal("-")) ))
        
        def exprssionParser(seq):
            seq.insert(0, 'code')
            for desc, expr in descAndExprs:
                seq = expr.parse(seq)
            del seq[0]
            return seq
            
        exprsionToken = Rex(r"^\d") | Or(*map(Literal, [ "+", "-", "*", "/", "(", ")" ]))
        expressionExpr = SubApply(exprssionParser, Repeat(exprsionToken, 0, None))
        statementExpr = Holder()
        statementExpr.expr = BuildToNode("s", Literal("print") + expressionExpr + Literal(";") | \
                Literal("if") + expressionExpr + Literal("then") + statementExpr + Literal("else") + statementExpr)
        
        removeSpaces = lambda seq: [] if len(seq) == 2 and seq[1] == ' ' else seq
        spaceRemoveExpr = SubApply(removeSpaces, Repeat(Any(), 0, None))
        
        text = "print 1*(3+4);"
        seq = [ 'code' ] + split_to_strings(text, re.compile(r"[a-z]+|(\d|[.])+|[-+*/%()?:,;]|\[|\]"))
        seq = spaceRemoveExpr.parse(seq)
        seq = statementExpr.parse(seq)
        seq_wo_attr = seq_remove_strattrs(seq) 
        print "\n".join(seq_pretty(seq_wo_attr))
        self.assertTrue(seq_wo_attr[1][0] == 's')
        s = seq_wo_attr[1]
        self.assertTrue(s[1] == 'print')
        self.assertTrue(s[2][0] == 't')
        self.assertTrue(s[3] == ';')

        text = "if -1 then print -1; else print 1;"
        seq = [ 'code' ] + split_to_strings(text, re.compile(r"[a-z]+|(\d|[.])+|[-+*/%()?:,;]|\[|\]"))
        seq = spaceRemoveExpr.parse(seq)
        seq = statementExpr.parse(seq)
        seq_wo_attr = seq_remove_strattrs(seq) 
        print "\n".join(seq_pretty(seq_wo_attr))
        self.assertTrue(seq_wo_attr[1][0] == 's')
        s = seq_wo_attr[1]
        self.assertTrue(s[1] == 'if')
        self.assertTrue(s[3] == 'then')
        self.assertTrue(s[5] == 'else')
        
if __name__ == '__main__':
    unittest.main()
