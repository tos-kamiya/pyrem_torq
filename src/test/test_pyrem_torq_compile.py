'''
Created on 2009/07/22

@author: kamiya
'''

import sys

import pyrem_torq.script
import pyrem_torq.expression
import pyrem_torq.treeseq

import unittest

def compiling(exprLine):
    print "exprLine=", exprLine
    try:
        seq = pyrem_torq.script.parse_to_ast(exprLine, sys.stderr)
    except pyrem_torq.expression.InterpretError, e:
        raise pyrem_torq.script.CompileError("pos %s: error: %s" % ( repr(e.stack), str(e) ), None)
    print "ast=", "\n".join(pyrem_torq.treeseq.seq_pretty(seq))
    expr = pyrem_torq.script.convert_to_expression_object(seq)
    print "expr=", expr
    return expr

class TestTorqComile(unittest.TestCase):
    def test1st(self):
        compiling('text :: (v <- +(r"^\d" | ".")) | (null <- +(" " | ">"));')
        
    def test2nd(self):
        compiling('text :: (v <- (null <- "("), +(@0 | req^("(" | ")"), any), (null <- ")"));')
    
    def test3rd(self):
        compiling('text :: ?(v <- (u_op <- "+" | "-"), (v :: ~@0)), *(req^(v), any, ?(v <- (u_op <- "+" | "-"), (v :: ~@0)) | (v :: ~@0));')
        
    def test4th(self):
        compiling('text :: ~(v <- (v :: ~@0), +((b_op <- "**"), (v :: ~@0))) | (v :: ~@0);')
    
    def test5th(self):
        compiling('text :: ~(v <- (v :: ~@0), +((b_op <- "*" | "/"), (v :: ~@0))) | (v :: ~@0);')

    def test6th(self):
        compiling('v :: ~@0;')
    
    def test7th(self):
        exprStr = """
    req(h"a"), req^(h"a")
    | (word <- +(h"a" | "_"))
    | (multiline_comment <- "/", "*" *(req^("*", "/"), any), "*", "/");
"""
        self.assertRaises(pyrem_torq.script.CompileError, compiling, exprStr)
    
#    def test8th(self):
#        exprStr = "insert(hoge)"
#        exprs = compiling(exprStr)
#        exprStr2 = "(hoge <-)"
#        exprs2 = compiling(exprStr)
#        self.assertTrue(exprs == exprs2)

    def test8th(self):
        exprStr = "(hoge <-), <>huga, (<>boo :: a), (<>foo :: ~b);"
        compiling(exprStr)
    
    def test9th(self):
        compiling('text :: ~?("a" | @0);')
    
    def test10th(self):
        compiling('text :: ~eof;')
    
    def test11th(self):
        compiling('text :: ~(any^(eof, a) | *any^(eof));')
    
    def test12th(self):
        compiling('text :: ~(a <- (<>b | <>c));')
        
    def test13th(self):
        compiling('text :: ~(ri"[a-z]" | i"f");')
    
    def test14th(self):
        compiling("hoge <- <>fuga;")
    
    def test15th(self):
        exprStr1 = "req^ a | b;"
        expr1 = compiling(exprStr1)
        exprStr2 = "req^(a | b);"
        expr2 = compiling(exprStr2)
        exprStr3 = "(req^ a) | b;"
        expr3 = compiling(exprStr3)
        self.assertNotEqual(expr1, expr2)
        self.assertEqual(expr1, expr3)
    
    def test16th(self):
        expr1 = compiling('"a", error("should not a");')
        expr2 = compiling('"a", error "should not a";')
        self.assertEqual(expr1, expr2)
        
    def test17th(self):
        self.assertRaises(pyrem_torq.script.CompileError, compiling, "a b;")
        self.assertRaises(pyrem_torq.script.CompileError, compiling, "a (b);")
        self.assertRaises(pyrem_torq.script.CompileError, compiling, "(a) (b);")
        self.assertRaises(pyrem_torq.script.CompileError, compiling, "(a) b;")
    
    def test18th(self):
        exprs = map(compiling, [ "", "\n", ";", ";\n" ])
        for e in exprs:
            self.assertEquals(e, None)

    def test19th(self):
        self.assertRaises(KeyError, compiling, "@undefined_label;")

if __name__ == '__main__':
    unittest.main()
    
