'''
Created on 2009/07/17

@author: kamiya
'''
import sys, os
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from pyrem_torq.treeseq import *
from pyrem_torq.expression import *

def mc4la_to_readable(r):
    if r is None: return None
    nodes, literals, epsilon = r.nodes, r.literals, r.emptyseq
    return (sorted(nodes) if nodes is not ANY_ITEM else None), (sorted(literals) if literals is not ANY_ITEM else None), epsilon

class TestTorqExpression(unittest.TestCase):
    def test1st(self):
        expr = Literal('ab')
        seq = [ 'text', 0, 'ab' ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(1 + posDelta, len(seq))
        self.assertEqual(outSeq, [ 0, 'ab' ])
    
    def testSeq(self):
        expr = Seq(Literal('a'), Literal('b'))
        seq = [ 'text', 0, 'a', 1, 'b' ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(1 + posDelta, len(seq))
        self.assertEqual(outSeq, [ 0, 'a', 1, 'b' ])

    def testOr(self):
        expr = Or(Literal('a'), Literal('b'))
        
        seq = [ 'text', 0, 'a' ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(1 + posDelta, len(seq))
        self.assertEqual(outSeq, [ 0, 'a' ])
        
        seq = [ 'text', 0, 'b' ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(1 + posDelta, len(seq))
        self.assertEqual(outSeq, [ 0, 'b' ])
        
    def testRepeat(self):
        expr = Repeat(Literal('a'), 3, 3)
        
        seq = [ 'text', 0, 'a', 1, 'a', 2, 'a' ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(1 + posDelta, len(seq))
        self.assertEqual(outSeq, [ 0, 'a', 1, 'a', 2, 'a' ])

        seq = [ 'text', 0, 'a', 1, 'a' ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 0)
        
        expr = Repeat(Literal('a'), 0, 3)
        
        seq = [ 'text' ]
        for i in xrange(10): seq.extend(( i, 'a' ))
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 6)
        self.assertEqual(outSeq, [ 0, 'a', 1, 'a', 2, 'a' ])
        
        seq = [ 'text', 0, 'a', 1, 'a' ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 4)
        self.assertEqual(outSeq, [ 0, 'a', 1, 'a' ])
    
        expr = Repeat(Literal('a'), 0, None)
        
        seq = [ 'text' ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 0)
        self.assertFalse(outSeq)
        
        seq = [ 'text', 0, 'a', 1, 'a' ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 4)
        self.assertEqual(outSeq, [ 0, 'a', 1, 'a' ])
    
    def testNodeMatch(self):
        expr = NodeMatch('A', Literal("a"))
        seq = [ 'text', [ 'A', 0, 'a' ] ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)
        self.assertEqual(outSeq, [ [ 'A', 0, 'a' ] ])
        
    def testNode(self):
        expr = Node('A')
        seq = [ 'text', [ 'A', 0, 'p', 1, 'a', 2, 'b', 3, 'q' ] ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)
        self.assertEqual(outSeq, [ [ 'A', 0, 'p', 1, 'a', 2, 'b', 3, 'q' ] ])
        
    def testAny(self):
        expr = Any()
        seq = [ 'text', [ 'A', 0, 'p', 1, 'a', 2, 'b', 3, 'q' ] ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)
        self.assertEqual(outSeq, [ [ 'A', 0, 'p', 1, 'a', 2, 'b', 3, 'q' ] ])
        
        seq = [ 'text', 0, 'a' ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 2)
        self.assertEqual(outSeq, [ 0, 'a' ])
        
    def testLiteralClass(self):
        expr = LiteralClass(("a", "b", "c"))
        seq = [ 'text', 0, 'a' ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 2)
        self.assertEqual(outSeq, [ 0, 'a' ])
        
        seq = [ 'text', 0, 'b' ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 2)
        self.assertEqual(outSeq, [ 0, 'b' ])

        seq = [ 'text', 0, 'p' ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 0)
        
    def testRex(self):
        expr = Rex(r"^[a-c]$")
        seq = [ 'text', 0, 'a' ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 2)
        self.assertEqual(outSeq, [ 0, 'a' ])
        
        seq = [ 'text', 0, 'd' ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertFalse(posDelta)
    
        seq = [ 'text', 0, u'a' ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 2)
        self.assertEqual(outSeq, [ 0, u'a' ])
        
    def testEpsilonConcatination(self):
        expr1 = Epsilon()
        expr2 = Literal("fuga")
        expr1_2 = expr1 + expr2
        self.assertNotEqual(expr1_2, Literal("fuga"))
    
    def testSelection(self):
        expr1 = LiteralClass(("u", "p"))
        expr2 = LiteralClass(("d", "o", "w", "n"))
        expr1_2 = expr1 | expr2
        self.assertNotEqual(expr1_2, LiteralClass(("u", "p", "d", "o", "w", "n")))
        
    def testConcatLiteal(self):
        expr1 = Literal("a")
        expr2 = Literal("b")
        expr1or2 = expr1 | expr2
        self.assertNotEqual(expr1or2, LiteralClass([ "a", "b" ]))
        
        expr1plus2 = expr1 + expr2
        self.assertNotEqual(expr1plus2, Seq(Literal("a"), Literal("b")))
        
    def testIdentifier(self):
        idExpr = Literal('_') + [0,]*(Literal('_') | \
                Rex(r"^[a-zA-Z]") | \
                Rex(r"^[0-9]")) | \
                Rex(r"^[a-zA-Z]") + [0,]*(Literal('_') | Rex(r"^[a-zA-Z]") | Rex(r"^[0-9]"))
        seq = [ 'text', 0, 'abc' ]
        
        posDelta, outSeq = idExpr.match(seq, 1)
        self.assertEqual(posDelta, 2)
        self.assertEqual(outSeq, [ 0, 'abc' ])
        
    def testRepeat2(self):
        expr = Repeat(InsertNode('hoge'), 3, 3)
        seq = [ 'text' ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 0)
        self.assertEqual(outSeq, [ [ 'hoge' ], [ 'hoge' ], [ 'hoge' ] ])
        
        expr = Repeat(InsertNode('hoge'), 3, 3) + Literal('a')
        seq = [ 'text', 0, 'a' ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 2)
        self.assertEqual(outSeq, [ [ 'hoge' ], [ 'hoge' ], [ 'hoge' ], 0, 'a' ])
        
    def testAnyLiteral(self):
        expr = Repeat(AnyLiteral(), 0, None)
        seq = [ 'text', 0, "a", 1, "b", 2, "c" ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 6)
        self.assertEqual(outSeq, [ 0, "a", 1, "b", 2, "c" ])
        
    def testAnyNode(self):
        expr = Repeat(AnyNode(), 0, None)
        seq = [ 'text', [ 'a' ], [ 'b' ], [ 'c' ] ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 3)
        self.assertEqual(outSeq, [ [ 'a' ], [ 'b' ], [ 'c' ] ])
    
        seq = [ 'code', 0, 'a', 1, 'b', 2, 'c' ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 0)
        
    def testAnyNodeMatch(self):
        expr = Repeat(AnyNodeMatch(Literal('X')), 0, None)
        seq = [ 'text', [ 'a', 0, 'X' ], [ 'b', 1, 'X' ], [ 'c', 2, 'Y' ] ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 2)
        self.assertEqual(outSeq, [ [ 'a', 0, 'X' ], [ 'b', 1, 'X' ] ])
        
    def testReqs(self):        
        expr = Require(Node("a"))
        self.assertEqual(mc4la_to_readable(expr.getMatchCandidateForLookAhead()), 
                ( [ 'a' ], [], False ))
        
        expr = Require(Literal("a"))
        self.assertEqual(mc4la_to_readable(expr.getMatchCandidateForLookAhead()), 
                ( [], [ 'a' ], False ))
        
        expr = Seq(Repeat(Literal("a"), 0, 1), Literal("b"))
        self.assertEqual(mc4la_to_readable(expr.getMatchCandidateForLookAhead()), 
                ( [], [ 'a', 'b' ], False ))

        expr = Or(Literal('a'), Literal('b'))
        self.assertEqual(mc4la_to_readable(expr.getMatchCandidateForLookAhead()), 
                ( [], [ 'a', 'b' ], False ))
                
        expr = Or(
                  Seq(
                      Repeat(Literal("a"), 0, 1), 
                      Literal("b")), 
                  Literal("c"))
        self.assertEqual(mc4la_to_readable(expr.getMatchCandidateForLookAhead()), 
                ( [], [ 'a', 'b', 'c' ], False ))
    
    def testSearch(self):
        expr = Search(Seq(InsertNode("here"), Literal("a")))
        seq = [ 'text', 0, "a", 1, "b", 2, "c", 3, "a" ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 8)
        self.assertEqual(outSeq, [ [ "here" ], 0, "a", 1, "b", 2, "c", [ "here" ], 3, "a" ])
        
        expr = Repeat(Or(Seq(InsertNode("here"), Literal("a")), Any()), 0, None)
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 8)
        self.assertEqual(outSeq, [ [ "here" ], 0, "a", 1, "b", 2, "c", [ "here" ], 3, "a" ])
        
    def testSearch2(self):
        expr = Search(InsertNode("here"))
        seq = [ 'text', 0, "a", 1, "b", 2, "c" ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 6)
        self.assertEqual(outSeq, [ [ "here" ], 0, "a", [ "here" ], 1, "b", [ "here" ], 2, "c", [ "here" ] ])
        
        e1 = Or(InsertNode("here"), Any())
        expr = Repeat(e1, 0, None)
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 0)
        self.assertEqual(outSeq, [ ])

    def testNodeInsideNode(self):        
        expr = NodeMatch("expr", Node("expr") | Node("literal"))
        seq = [ 'code', [ 'expr', [ 'expr' ] ] ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)

    def testRemoveRedundantParen(self):
        expr0 = Holder()
        expr0.expr = Or(
                Require(NodeMatch("expr", Node("expr") | Node("literal"))) + Flattened(NodeMatch("expr", expr0)),
                NodeMatch("expr", Search(expr0)),
                Any())
        expr = Search(expr0)
        
        seq = [ 'code', [ 'expr', [ 'literal', 0, 'a' ] ] ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)
        outSeq2 = [ seq[0] ] + outSeq
        self.assertEqual(outSeq2, [ 'code', [ 'literal', 0, 'a' ] ])
        
        seq = [ 'code', [ 'expr', [ 'expr', [ 'literal', 0, 'a' ] ] ] ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)
        outSeq2 = [ seq[0] ] + outSeq
        self.assertEqual(outSeq2, [ 'code', [ 'literal', 0, 'a' ] ])
        
    def testCheckingLeftRecursion(self):
        expr2 = Holder()
        expr1 = Or(expr2, Literal('a'))
        expr2.expr = expr1
        self.assertTrue(expr2.isLeftRecursive())
        self.assertTrue(expr1.isLeftRecursive())
        
        expr3 = Or(Literal('a'), expr1)
        self.assertFalse(expr3.isLeftRecursive()) # expr3 includes a left-recursion expr, but expr3 itself is not left recursive.
        
        includesLeftRecursiveExpressions = any(e.isLeftRecursive() for e in expr3.extract_exprs())
        self.assertTrue(includesLeftRecursiveExpressions)

        expr = Or(Literal('b'), Literal('a'))
        self.assertFalse(expr.isLeftRecursive())
        
        expr = Holder()
        with self.assertRaises(LeftRecursionUndecided):        
            expr.isLeftRecursive() # expr's inner expression is not assigned yet, thus undecidable.
        
    def testFlattening(self):
        expr = BuildToNode("lc", Flattened(Node("c")))
        
        seq = [ 'code', [ 'c', 0, 'a' ] ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)
        outSeq2 = [ seq[0] ] + outSeq
        self.assertEqual(outSeq2, [ 'code', [ 'lc', 0, 'a' ] ])
        
    def testInsertNode(self):
        expr = Seq(Node("c"), InsertNode("X"), Node("a"))

        seq = [ 'code', [ 'c' ], [ 'a' ] ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 2)
        outSeq2 = [ seq[0] ] + outSeq
        self.assertEqual(outSeq2, [ 'code', [ 'c' ], [ 'X' ], [ 'a' ] ])
        
    def testInnerExprProperties(self):
        a = Node('a'); b = Node('b')
        singleExprs = [ Repeat(a, 0, 1), Search(a), Holder(), 
                Relabeled('c', a), Flattened(a), NodeMatch('c', a), AnyNodeMatch(a), BuildToNode('c', a) ]
        multipleExprs = [ Or(a, b), Seq(a, b) ]
        for e in singleExprs + multipleExprs:
            self.assertTrue(hasattr(e, "extract_exprs"))
        for e in singleExprs:
            self.assertTrue(hasattr(e, "expr"))
        for e in multipleExprs:
            self.assertTrue(hasattr(e, "exprs"))
    
    def testNodeExprProperties(self):
        nodeExprs = [ Node('a'), NodeMatch('a', Epsilon()) ]
        for ne in nodeExprs:
            self.assertTrue(hasattr(ne, "label"))
            self.assertTrue(hasattr(ne, "extract_labels"))
        
        nodeClassExpr = NodeClass(['a', 'b', 'c'])
        self.assertTrue(hasattr(nodeClassExpr, "labels"))
        self.assertTrue(hasattr(nodeClassExpr, "extract_labels"))
            
        newLabelExprs = [ Relabeled('newa', Node('a')), InsertNode('a'), BuildToNode('a', Epsilon()) ]
        for nle in newLabelExprs:
            self.assertTrue(hasattr(nle, "newLabel"))

    def testUpdateMC4LAWithRecursion(self):
        h = Holder()
        e = Or(Seq(Literal('a'), h), Literal('b'))
        h.expr = e
        self.assertEqual(mc4la_to_readable(e.getMatchCandidateForLookAhead()), 
                ( [], [ 'a', 'b' ], False ))
        self.assertEqual(mc4la_to_readable(h.getMatchCandidateForLookAhead()), 
                ( [], [ 'a', 'b' ], False ))

def TestSuite(TestTorqExpression):
    return unittest.makeSuite(TestTorqExpression)

if __name__ == '__main__':
    unittest.main()

