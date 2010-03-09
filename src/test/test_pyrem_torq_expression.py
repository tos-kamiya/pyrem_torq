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
        seq = [ 'text', 'ab' ]
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(1 + posDelta, len(seq))
        self.assertEqual(outSeq, [ 'ab' ])
        self.assertFalse(dropSeq)
    
    def testSeq(self):
        expr = Seq(Literal('a'), Literal('b'))
        seq = [ 'text', 'a', 'b' ]
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(1 + posDelta, len(seq))
        self.assertEqual(outSeq, [ 'a', 'b' ])
        self.assertFalse(dropSeq)

    def testOr(self):
        expr = Or(Literal('a'), Literal('b'))
        
        seq = [ 'text', 'a' ]
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(1 + posDelta, len(seq))
        self.assertEqual(outSeq, [ 'a' ])
        self.assertFalse(dropSeq)
        
        seq = [ 'text', 'b' ]
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(1 + posDelta, len(seq))
        self.assertEqual(outSeq, [ 'b' ])
        self.assertFalse(dropSeq)
    
    def testRepeat(self):
        expr = Repeat(Literal('a'), 3, 3)
        
        seq = [ 'text', 'a', 'a', 'a' ]
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(1 + posDelta, len(seq))
        self.assertEqual(outSeq, [ 'a' ] * 3)
        self.assertFalse(dropSeq)

        seq = [ 'text', 'a', 'a' ]
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 0)
        
        expr = Repeat(Literal('a'), 0, 3)
        
        seq = [ 'text' ] + [ 'a' ] * 10
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 3)
        self.assertEqual(outSeq, [ 'a' ] * 3)
        self.assertFalse(dropSeq)
        
        seq = [ 'text', 'a', 'a' ]
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 2)
        self.assertEqual(outSeq, [ 'a' ] * 2)
        self.assertFalse(dropSeq)
    
        expr = Repeat(Literal('a'), 0, None)
        
        seq = [ 'text' ]
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 0)
        self.assertFalse(outSeq)
        self.assertFalse(dropSeq)
        
        seq = [ 'text', 'a', 'a' ]
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 2)
        self.assertEqual(outSeq, [ 'a' ] * 2)
        self.assertFalse(dropSeq)
    
    def testNodeMatch(self):
        expr = NodeMatch('A', Literal("a"))
        seq = [ 'text', [ 'A', 'a' ] ]
        
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)
        self.assertEqual(outSeq, [ [ 'A', 'a' ] ])
        self.assertFalse(dropSeq)

    def testNode(self):
        expr = Node('A')
        seq = [ 'text', [ 'A', 'p', 'a', 'b', 'q' ] ]
        
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)
        self.assertEqual(outSeq, [ [ 'A', 'p', 'a', 'b', 'q' ] ])
        self.assertFalse(dropSeq)
        
    def testAny(self):
        expr = Any()
        seq = [ 'text', [ 'A', 'p', 'a', 'b', 'q' ] ]
        
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)
        self.assertEqual(outSeq, [ [ 'A', 'p', 'a', 'b', 'q' ] ])
        self.assertFalse(dropSeq)
        
        seq = [ 'text', 'a' ]
        
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)
        self.assertEqual(outSeq, [ 'a' ])
        self.assertFalse(dropSeq)

    def testLiteralClass(self):
        expr = LiteralClass(("a", "b", "c"))
        seq = [ 'text', 'a' ]
        
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)
        self.assertEqual(outSeq, [ 'a' ])
        self.assertFalse(dropSeq)
    
        seq = [ 'text', 'b' ]
        
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)
        self.assertEqual(outSeq, [ 'b' ])
        self.assertFalse(dropSeq)

        seq = [ 'text', 'p' ]
        
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 0)
    
    def testDrop(self):
        expr = Drop(Node("A"))
        
        seq = [ 'text', [ 'A' ] ]
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)
        self.assertFalse(outSeq)
        self.assertEqual(dropSeq, [ [ 'A' ] ])
        
    def testRex(self):
        expr = Rex(r"^[a-c]$")
        seq = [ 'text', 'a' ]
        
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)
        self.assertEqual(outSeq, [ 'a' ])
        self.assertFalse(dropSeq)
        
        seq = [ 'text', 'd' ]
        pos, outSeq, dropSeq = expr.match(seq, 1)
        self.assertFalse(pos)
    
        seq = [ 'text', u'a' ]
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)
        self.assertEqual(outSeq, [ u'a' ])
        self.assertFalse(dropSeq)
        
    def testEpsilonConcatination(self):
        expr1 = Epsilon()
        expr2 = Literal("fuga")
        expr1_2 = expr1 + expr2
        self.assertEqual(expr1_2, Literal("fuga"))
    
    def testSelection(self):
        expr1 = LiteralClass(("u", "p"))
        expr2 = LiteralClass(("d", "o", "w", "n"))
        expr1_2 = expr1 | expr2
        self.assertEqual(expr1_2, LiteralClass(("u", "p", "d", "o", "w", "n")))
        
    def testConcatLiteal(self):
        expr1 = Literal("a")
        expr2 = Literal("b")
        expr1or2 = expr1 | expr2
        self.assertEqual(expr1or2, LiteralClass([ "a", "b" ]))
        
        expr1plus2 = expr1 + expr2
        self.assertEqual(expr1plus2, Seq(Literal("a"), Literal("b")))
        
    def testIdentifier(self):
        idExpr = Literal('_') + [0,]*(Literal('_') | Rex(r"^[a-zA-Z]") | Rex(r"^[0-9]")) | \
                Rex(r"^[a-zA-Z]") + [0,]*(Literal('_') | Rex(r"^[a-zA-Z]") | Rex(r"^[0-9]"))
        seq = [ 'text', 'abc' ]
        
        posDelta, outSeq, dropSeq = idExpr.match(seq, 1)
        self.assertEqual(posDelta, 1)
        self.assertEqual(outSeq, [ 'abc' ])
        self.assertFalse(dropSeq)
    
    def testRepeat2(self):
        expr = Repeat(InsertNode('hoge'), 3, 3)
        seq = [ 'text' ]
        
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 0)
        self.assertEqual(outSeq, [ [ 'hoge' ], [ 'hoge' ], [ 'hoge' ] ])
        self.assertFalse(dropSeq)
    
        expr = Repeat(InsertNode('hoge'), 3, 3) + Literal('a')
        seq = [ 'text', 'a' ]
        
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)
        self.assertEqual(outSeq, [ [ 'hoge' ], [ 'hoge' ], [ 'hoge' ], 'a' ])
        self.assertFalse(dropSeq)
    
    def testAnyLiteral(self):
        expr = Repeat(AnyLiteral(), 0, None)
        seq = [ 'text', "a", "b", "c" ]
        
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 3)
        self.assertEqual(outSeq, [ "a", "b", "c" ])
        self.assertFalse(dropSeq)
    
    def testAnyNode(self):
        expr = Repeat(AnyNode(), 0, None)
        seq = [ 'text', [ 'a' ], [ 'b' ], [ 'c' ] ]
        
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 3)
        self.assertEqual(outSeq, [ [ 'a' ], [ 'b' ], [ 'c' ] ])
        self.assertFalse(dropSeq)
    
    def testAnyNodeMatch(self):
        expr = Repeat(AnyNodeMatch(Literal('X')), 0, None)
        seq = [ 'text', [ 'a', 'X' ], [ 'b', 'X' ], [ 'c', 'Y' ] ]
        
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 2)
        self.assertEqual(outSeq, [ [ 'a', 'X' ], [ 'b', 'X' ] ])
        self.assertFalse(dropSeq)
    
    def testReqs(self):
        def nomalize(r):
            if r is None: return None
            nodes, literals, epsilon = r
            return list(nodes), list(literals), epsilon
        
        expr = Req(Node("a"))
        self.assertEqual(nomalize(expr.required_node_literal_epsilon()), 
                ( [ 'a' ], [], False ))
        
        expr = Req(Literal("a"))
        self.assertEqual(nomalize(expr.required_node_literal_epsilon()), 
                ( [], [ 'a' ], False ))
        
        expr = Seq(Repeat(Literal("a"), 0, 1), Literal("b"))
        self.assertEqual(nomalize(expr.required_node_literal_epsilon()), 
                ( [], [ 'a', 'b' ], False ))

        expr = Or(Seq(Repeat(Literal("a"), 0, 1), Literal("b")), Literal("c"))
        self.assertEqual(nomalize(expr.required_node_literal_epsilon()), 
                ( [], [ 'a', 'b', 'c' ], False ))
    
    def testSearch(self):
        expr = Search(Seq(InsertNode("here"), Literal("a")))
        seq = [ 'text', "a", "b", "c", "a" ]
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 4)
        self.assertEqual(outSeq, [ [ "here" ], "a", "b", "c", [ "here" ], "a" ])

        expr = Repeat(Or(Seq(InsertNode("here"), Literal("a")), Any()), 0, None)
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 4)
        self.assertEqual(outSeq, [ [ "here" ], "a", "b", "c", [ "here" ], "a" ])
        
    def testSearch2(self):
        expr = Search(InsertNode("here"))
        seq = [ 'text', "a", "b", "c" ]
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 3)
        self.assertEqual(outSeq, [ [ "here" ], "a", [ "here" ], "b", [ "here" ], "c", [ "here" ] ])

        expr = Repeat(Or(InsertNode("here"), Any()), 0, None)
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 0)
        self.assertEqual(outSeq, [ ])
    
    def testRemoveRedundantParen(self):
        expr = Or(Req(NodeMatch("expr", Node("expr") | Node("literal"))) + NodeMatch("expr", Marker('0'), newLabel=FLATTEN),
            NodeMatch("expr", Search(Marker('0'))),
            Any())
        assign_marker_expr(expr, '0', expr)
        expr = Search(expr)
        
        seq = [ 'code', [ 'expr', [ 'literal', 'a' ] ] ]
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)
        outSeq = [ seq[0] ] + outSeq
        self.assertEqual(outSeq, [ 'code', [ 'literal', 'a' ] ])

        seq = [ 'code', [ 'expr', [ 'expr', [ 'literal', 'a' ] ] ] ]
        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(posDelta, 1)
        outSeq = [ seq[0] ] + outSeq
        self.assertEqual(outSeq, [ 'code', [ 'literal', 'a' ] ])

def TestSuite(TestTorqExpression):
    return unittest.makeSuite(TestTorqExpression)

if __name__ == '__main__':
    unittest.main()

