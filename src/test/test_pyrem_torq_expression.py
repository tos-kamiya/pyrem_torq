'''
Created on 2009/07/17

@author: kamiya
'''

import unittest

from pyrem_torq.treeseq import *
from pyrem_torq.expression import *

class TestTorqExpression(unittest.TestCase):
    def test1st(self):
        expr = Literal('ab')
        seq = [ 'text', 0, 'ab' ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(1 + posDelta, len(seq))
        self.assertEqual(outSeq, [ 0, 'ab' ])
    
        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
        
    def testSeq(self):
        expr = Seq(Literal('a'), Literal('b'))
        seq = [ 'text', 0, 'a', 1, 'b' ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(1 + posDelta, len(seq))
        self.assertEqual(outSeq, [ 0, 'a', 1, 'b' ])

        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
        
    def testOr(self):
        expr = Or(Literal('a'), Literal('b'))
        
        seq = [ 'text', 0, 'a' ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(1 + posDelta, len(seq))
        self.assertEqual(outSeq, [ 0, 'a' ])
        
        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
       
        seq = [ 'text', 0, 'b' ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(1 + posDelta, len(seq))
        self.assertEqual(outSeq, [ 0, 'b' ])
    
        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
        
    def testRepeat(self):
        expr = Repeat(Literal('a'), 3, 3)
        
        seq = [ 'text', 0, 'a', 1, 'a', 2, 'a' ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(1 + posDelta, len(seq))
        self.assertEqual(outSeq, [ 0, 'a', 1, 'a', 2, 'a' ])

        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))

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

        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
        
    def testNode(self):
        expr = Node('A')
        seq = [ 'text', [ 'A', 0, 'p', 1, 'a', 2, 'b', 3, 'q' ] ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)
        self.assertEqual(outSeq, [ [ 'A', 0, 'p', 1, 'a', 2, 'b', 3, 'q' ] ])
        
        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
        
    def testAny(self):
        expr = Any()
        seq = [ 'text', [ 'A', 0, 'p', 1, 'a', 2, 'b', 3, 'q' ] ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)
        self.assertEqual(outSeq, [ [ 'A', 0, 'p', 1, 'a', 2, 'b', 3, 'q' ] ])
        
        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
        
        seq = [ 'text', 0, 'a' ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 2)
        self.assertEqual(outSeq, [ 0, 'a' ])

        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
        
    def testLiteralClass(self):
        expr = LiteralClass(("a", "b", "c"))
        seq = [ 'text', 0, 'a' ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 2)
        self.assertEqual(outSeq, [ 0, 'a' ])
    
        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
        
        seq = [ 'text', 0, 'b' ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 2)
        self.assertEqual(outSeq, [ 0, 'b' ])

        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))

        seq = [ 'text', 0, 'p' ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 0)
    
        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
        
    def testRex(self):
        expr = Rex(r"^[a-c]$")
        seq = [ 'text', 0, 'a' ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 2)
        self.assertEqual(outSeq, [ 0, 'a' ])
        
        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
        
        seq = [ 'text', 0, 'd' ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertFalse(posDelta)
    
        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
        
        seq = [ 'text', 0, u'a' ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 2)
        self.assertEqual(outSeq, [ 0, u'a' ])
        
        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
        
    def testEpsilonConcatination(self):
        expr1 = Epsilon()
        expr2 = Literal("fuga")
        expr1_2 = expr1 + expr2
        self.assertNotEqual(expr1_2, Literal("fuga"))
        expr1_2 = expr1_2.optimized()
        self.assertEqual(expr1_2, Literal("fuga"))
    
    def testSelection(self):
        expr1 = LiteralClass(("u", "p"))
        expr2 = LiteralClass(("d", "o", "w", "n"))
        expr1_2 = expr1 | expr2
        self.assertNotEqual(expr1_2, LiteralClass(("u", "p", "d", "o", "w", "n")))
        expr1_2 = expr1_2.optimized()
        self.assertEqual(expr1_2, LiteralClass(("u", "p", "d", "o", "w", "n")))
        
    def testConcatLiteal(self):
        expr1 = Literal("a")
        expr2 = Literal("b")
        expr1or2 = expr1 | expr2
        self.assertNotEqual(expr1or2, LiteralClass([ "a", "b" ]))
        expr1or2 = expr1or2.optimized()
        self.assertEqual(expr1or2, LiteralClass([ "a", "b" ]))
        
        expr1plus2 = expr1 + expr2
        self.assertNotEqual(expr1plus2, Seq(Literal("a"), Literal("b")))
        expr1plus2 = expr1plus2.optimized()
        self.assertEqual(expr1plus2, Seq(Literal("a"), Literal("b")))
        
    def testIdentifier(self):
        idExpr = Literal('_') + [0,]*(Literal('_') | \
                Rex(r"^[a-zA-Z]") | \
                Rex(r"^[0-9]")) | \
                Rex(r"^[a-zA-Z]") + [0,]*(Literal('_') | Rex(r"^[a-zA-Z]") | Rex(r"^[0-9]"))
        seq = [ 'text', 0, 'abc' ]
        
        posDelta, outSeq = idExpr.match(seq, 1)
        self.assertEqual(posDelta, 2)
        self.assertEqual(outSeq, [ 0, 'abc' ])
    
        oResult = idExpr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
        
    def testRepeat2(self):
        expr = Repeat(InsertNode('hoge'), 3, 3)
        seq = [ 'text' ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 0)
        self.assertEqual(outSeq, [ [ 'hoge' ], [ 'hoge' ], [ 'hoge' ] ])
    
        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
        
        expr = Repeat(InsertNode('hoge'), 3, 3) + Literal('a')
        seq = [ 'text', 0, 'a' ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 2)
        self.assertEqual(outSeq, [ [ 'hoge' ], [ 'hoge' ], [ 'hoge' ], 0, 'a' ])
    
        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
        
    def testAnyLiteral(self):
        expr = Repeat(AnyLiteral(), 0, None)
        seq = [ 'text', 0, "a", 1, "b", 2, "c" ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 6)
        self.assertEqual(outSeq, [ 0, "a", 1, "b", 2, "c" ])
    
        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
        
    def testAnyNode(self):
        expr = Repeat(AnyNode(), 0, None)
        seq = [ 'text', [ 'a' ], [ 'b' ], [ 'c' ] ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 3)
        self.assertEqual(outSeq, [ [ 'a' ], [ 'b' ], [ 'c' ] ])
    
        seq = [ 'code', 0, 'a', 1, 'b', 2, 'c' ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 0)
        
        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
        
    def testAnyNodeMatch(self):
        expr = Repeat(AnyNodeMatch(Literal('X')), 0, None)
        seq = [ 'text', [ 'a', 0, 'X' ], [ 'b', 1, 'X' ], [ 'c', 2, 'Y' ] ]
        
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 2)
        self.assertEqual(outSeq, [ [ 'a', 0, 'X' ], [ 'b', 1, 'X' ] ])
    
        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
        
    def testReqs(self):
        def nomalize(r):
            if r is None: return None
            nodes, literals, epsilon = r.nodes, r.literals, r.emptyseq
            return (list(nodes) if nodes is not None else None), (list(literals) if literals is not None else None), epsilon
        
        expr = Require(Node("a"))
        self.assertEqual(nomalize(expr.getMatchCandidateForLookAhead()), 
                ( [ 'a' ], [], False ))
        
        expr = Require(Literal("a"))
        self.assertEqual(nomalize(expr.getMatchCandidateForLookAhead()), 
                ( [], [ 'a' ], False ))
        
        expr = Seq(Repeat(Literal("a"), 0, 1), Literal("b"))
        self.assertEqual(nomalize(expr.getMatchCandidateForLookAhead()), 
                ( [], [ 'a', 'b' ], False ))

        expr = Or(
                  Seq(
                      Repeat(Literal("a"), 0, 1), 
                      Literal("b")), 
                  Literal("c"))
        self.assertEqual(nomalize(expr.getMatchCandidateForLookAhead()), 
                ( [], [ 'a', 'b', 'c' ], False ))
    
    def testSearch(self):
        expr = Search(Seq(InsertNode("here"), Literal("a")))
        seq = [ 'text', 0, "a", 1, "b", 2, "c", 3, "a" ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 8)
        self.assertEqual(outSeq, [ [ "here" ], 0, "a", 1, "b", 2, "c", [ "here" ], 3, "a" ])

        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
        
        expr = Repeat(Or(Seq(InsertNode("here"), Literal("a")), Any()), 0, None)
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 8)
        self.assertEqual(outSeq, [ [ "here" ], 0, "a", 1, "b", 2, "c", [ "here" ], 3, "a" ])
        
        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
        
    def testSearch2(self):
        expr = Search(InsertNode("here"))
        seq = [ 'text', 0, "a", 1, "b", 2, "c" ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 6)
        self.assertEqual(outSeq, [ [ "here" ], 0, "a", [ "here" ], 1, "b", [ "here" ], 2, "c", [ "here" ] ])

        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
        
        e1 = Or(InsertNode("here"), Any())
        expr = Repeat(e1, 0, None)
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 0)
        self.assertEqual(outSeq, [ ])
    
        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))

    def testNodeInsideNode(self):        
        expr = NodeMatch("expr", Node("expr") | Node("literal"))
        seq = [ 'code', [ 'expr', [ 'expr' ] ] ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)

    def testRemoveRedundantParen(self):
        expr0 = Holder()
        expr0.expr = Or(
                Require(NodeMatch("expr", Node("expr") | Node("literal"))) + NodeMatch("expr", expr0, newLabel=FLATTEN),
                NodeMatch("expr", Search(expr0)),
                Any())
        expr = Search(expr0)
        
        seq = [ 'code', [ 'expr', [ 'literal', 0, 'a' ] ] ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)
        outSeq2 = [ seq[0] ] + outSeq
        self.assertEqual(outSeq2, [ 'code', [ 'literal', 0, 'a' ] ])

        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
        
        seq = [ 'code', [ 'expr', [ 'expr', [ 'literal', 0, 'a' ] ] ] ]
        posDelta, outSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)
        outSeq2 = [ seq[0] ] + outSeq
        self.assertEqual(outSeq2, [ 'code', [ 'literal', 0, 'a' ] ])

        oResult = expr.optimized().match(seq, 1)
        self.assertEquals(oResult, ( posDelta, outSeq ))
        
    def testOptimizationThroughHolder(self):
        expr2 = Holder()
        expr1 = Literal("a")
        expr2.expr = expr1
        self.assertNotEqual(expr2, Literal("a"))
        expr2 = expr2.optimized()
        self.assertEqual(expr2, Literal("a"))
        
    def testOptimizationOfRecursiveExpression(self):
        expr2 = Holder()
        expr1 = Literal("a")
        expr2.expr = Or(Epsilon(), expr1)
        optimizedExpr2 = expr2.optimized()
        self.assertEqual(optimizedExpr2, Epsilon())
        
        expr3 = Holder()
        expr3.expr = Or(expr1, Epsilon())
        optimizedExpr3 = expr3.optimized()
        self.assertEqual(optimizedExpr3, expr3.expr)
    
#    def testCheckingLeftRecursion(self):
#        expr2 = Holder()
#        expr1 = Or(expr2, Literal('a'))
#        expr2.expr = expr1
#        optimizedExpr2 = expr2.optimized()

def TestSuite(TestTorqExpression):
    return unittest.makeSuite(TestTorqExpression)

if __name__ == '__main__':
    unittest.main()

