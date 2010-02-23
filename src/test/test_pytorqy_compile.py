'''
Created on 2009/07/22

@author: kamiya
'''

import sys

import pytorqy.compile
import pytorqy.expression
import pytorqy.treeseq

import unittest

def compiling(exprLine):
    print "exprLine=", exprLine
    try:
        seq = pytorqy.compile.parse_to_ast(exprLine, sys.stderr)
    except pytorqy.expression.InterpretError as e:
        raise pytorqy.compile.CompileError("pos %s: error: %s" % ( repr(e.stack), str(e) ), None)
    print "ast=", "\n".join(pytorqy.treeseq.seq_pretty(seq))
    exprs = pytorqy.compile.convert_to_expression_object(seq)
    print "exprs=", exprs
    return exprs

class TestPytorqyComile(unittest.TestCase):
    def test1st(self):
        compiling('text :: (v <- +(r"^\d" | ".")) | (null <- +(" " | ">"));')
        
    def test2nd(self):
        compiling('text :: (v <- (null <- "("), +(@0 | xcp("(" | ")"), any), (null <- ")"));')
    
    def test3rd(self):
        compiling('text :: ?(v <- (u_op <- "+" | "-"), (v :: ~@0)), *(xcp(v), any, ?(v <- (u_op <- "+" | "-"), (v :: ~@0)) | (v :: ~@0));')
        
    def test4th(self):
        compiling('text :: ~(v <- (v :: ~@0), +((b_op <- "**"), (v :: ~@0))) | (v :: ~@0);')
    
    def test5th(self):
        compiling('text :: ~(v <- (v :: ~@0), +((b_op <- "*" | "/"), (v :: ~@0))) | (v :: ~@0);')

    def test6th(self):
        compiling('v :: ~@0;')
    
    def test7th(self):
        exprStr = """
    req(h"a"), xcp(h"a")
    | (word <- +(h"a" | "_"))
    | (multiline_comment <- "/", "*" *(xcp("*", "/"), any), "*", "/");
"""
        self.assertRaises(pytorqy.compile.CompileError, compiling, exprStr)
    
#    def test8th(self):
#        exprStr = "insert(hoge)"
#        exprs = compiling(exprStr)
#        exprStr2 = "(hoge <-)"
#        exprs2 = compiling(exprStr)
#        self.assertTrue(exprs == exprs2)

    def test9th(self):
        exprStr = "(hoge <-), <>huga, (<>boo :: a), (<>foo :: ~b);"
        compiling(exprStr)
    
    def test10th(self):
        compiling('text :: ~?("a" | @0);')
    
    def test11th(self):
        compiling('text :: ~eof;')
    
    def test12th(self):
        compiling('text :: ~(any^(eof, a) | *any^(eof));')
    
    def test13th(self):
        compiling('text :: ~(a <- (<>b | <>c));')
        
    def test14th(self):
        exprs = compiling('text :: ~(ri"[a-z]" | i"f");')
    
    def test15th(self):
        exprs = compiling("hoge <- <>fuga;")
        assert len(exprs) == 1
    
    def test16th(self):
        exprStr1 = "xcp a | b;"
        exprs1 = compiling(exprStr1)
        exprStr2 = "xcp(a | b);"
        exprs2 = compiling(exprStr2)
        exprStr3 = "(xcp a) | b;"
        exprs3 = compiling(exprStr3)
        self.assertNotEqual(exprs1, exprs2)
        self.assertEqual(exprs1, exprs3)
    
if __name__ == '__main__':
    unittest.main()
    
