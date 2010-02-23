import sys, re

from pytorqy.utility import split_to_strings_iter
import pytorqy.expression
import pytorqy.compile
import pytorqy.treeseq

import unittest

to_gsublike_expr = pytorqy.expression.Search.build

def my_compile(exprStr, recursionAtMarker0=True):
    try:
        seq = pytorqy.compile.parse_to_ast(exprStr, sys.stderr)
    except pytorqy.expression.InterpretError as e:
        raise pytorqy.compile.CompileError, "pos %s: error: %s" % ( repr(e.stack), str(e) )
    #print "ast=", "\n".join(pytorqy.treeseq.seq_pretty(seq))
    
    exprs = pytorqy.compile.convert_to_expression_object(seq)
    
    if recursionAtMarker0:
        for expr in exprs:
            expr.replace_marker_expr("0", expr)
    
    return exprs

def compile_exprs(exprStrs):
    exprs = []
    for exprStr in exprStrs:
        expr = pytorqy.compile.compile(exprStr, recursionAtMarker0=True)
        #expr = my_compile(exprStr, recursiionAtMarker0=True)
        
        assert len(expr) == 1
        expr = expr[0]
        exprs.append(expr)
    return exprs

class TestPytorqyComileAndInterpret(unittest.TestCase):
    def test1st(self):
        exprStrs = [ 
            r'~((v <- +(r"^\d" | ".")) | (null <- +(" " | "\t")));',
            r'~(v <- (null <- "("), +(@0 | xcp("(" | ")"), any), (null <- ")"));',
            r"""
                ?(v <- (u_op <- "+" | "-"), (v :: ~@0)), 
                *(
                    (v :: ~@0), *("+" | "-") 
                    | (v <- (u_op <- "+" | "-"), (v :: ~@0))
                    | any
                );
            """,
            r'~((v <- (v :: ~@0), +((b_op <- "**"), (v :: ~@0))) | (v :: ~@0));',
            r'~((v <- (v :: ~@0), +((b_op <- "*" | "/"), (v :: ~@0))) | (v :: ~@0));', 
            r'~((v <- (v :: ~@0), +((b_op <- "+" | "-"), (v :: ~@0))) | (v :: ~@0));',
        ]
        exprs = compile_exprs(exprStrs)
        
        seq = [ 'code' ]; seq.extend(split_to_strings_iter("+1.0 + 2 * ((3 - 4) / -.5) ** 6"))
        for exprIndex, expr in enumerate(exprs):
            print "exprIndex=", exprIndex, "cur seq=", "\n".join(pytorqy.treeseq.seq_pretty(seq))
            posDelta, outSeq, dropSeq = expr.match(seq, 1)
            self.assertEqual(1 + posDelta, len(seq))
            seq = [ seq[0] ] + outSeq
        print "result seq=", "\n".join(pytorqy.treeseq.seq_pretty(seq))
        
    def test3rd(self):
        exprStrs = [
            r'~(eol <- "\t" | "\f" | "\v" | "\r" | "\n");',
            r'~(comment <- "/", "*", *(+"*", (xcp("/"), any) | xcp("*"), any), +"*", "/");',
            r'~(comment <- "/", "/", *(xcp(eol), any));',
        ]
        exprs = compile_exprs(exprStrs)
        
        inputText = """
#include <stdio.h> // import printf()

int main(int argc, char *argv[])
{
    /************************
     ** the arguments argc/**
     ** argv are not used. **
     ************************/
    
    printf("hello, world.\n");
    return 0;
}
"""[1:-1]

        seq = [ 'code' ]; seq.extend(split_to_strings_iter(inputText))
        for expr in exprs:
            posDelta, outSeq, dropSeq = expr.match(seq, 1)
            self.assertEqual(1 + posDelta, len(seq))
            seq = [ seq[0] ] + outSeq
        print "result seq=", "\n".join(pytorqy.treeseq.seq_pretty(seq))
    
    def test4th(self):
        IN = pytorqy.expression.InsertNode.build
        BtN = pytorqy.expression.BuildToNode.build
        L = pytorqy.expression.Literal.build
        A = pytorqy.expression.Any.build
        Q = pytorqy.expression.Req.build
        S = pytorqy.expression.Search.build
        
        eolExpr = BtN('eol', L("\r\n") | L("\n") | L("\r"))
        expr = S(eolExpr) + Q(pytorqy.expression.EndOfNode()) + IN('eof')
        
        seq = [ 'code' ]; seq.extend(split_to_strings_iter("abc\n"))

        posDelta, outSeq, dropSeq = expr.match(seq, 1)
        self.assertEqual(1 + posDelta, 3)
        self.assertEqual(outSeq, [ 'abc', [ 'eol', '\n' ], [ 'eof' ] ])
    
    def test5th(self):
        atoz = 'r"^[a-z]"'
        exprStrs = [ r'~(req(%(atoz)s), ((op_logical_and <- "and") | (op_logical_or <- "or")), xcp(%(atoz)s));' % { 'atoz': atoz } ]
        
        exprs = compile_exprs(exprStrs)
        
        inputText = r'if (x and y or z) printf("hello\n");'
        inputText = inputText.decode(sys.getfilesystemencoding())
        seq = [ 'code' ]; seq.extend(split_to_strings_iter(inputText))
        
        for expr in exprs:
            posDelta, outSeq, dropSeq = expr.match(seq, 1)
            self.assertEqual(1 + posDelta, len(seq))
            seq = [ seq[0] ] + outSeq
        
        foundAnd, foundOr = False, False
        for item in seq:
            if isinstance(item, list):
                if item[0:1] == [ 'op_logical_and' ]: foundAnd = True
                if item[0:1] == [ 'op_logical_or' ]: foundOr = True
        self.assertTrue(foundAnd)
        self.assertTrue(foundOr)
                    
        print "result seq=", "\n".join(pytorqy.treeseq.seq_pretty(seq))
    
    def test6th(self):
        searchWordLike = r'~(wordlike <- "_", *(r"^[a-zA-Z]" | r"\d" | "_") | r"^[a-zA-Z]", *(r"^[a-zA-Z]" | r"\d" | "_"));'
        exprs = compile_exprs([ searchWordLike ])
        assert len(exprs) == 1
        
        inputText = r'argv[0];'
        inputText = inputText.decode(sys.getfilesystemencoding())
        seq = [ 'code' ]; seq.extend(split_to_strings_iter(inputText))
        
        posDelta, outSeq, dropSeq = exprs[0].match(seq, 1)
        self.assertEqual(1 + posDelta, len(seq))
        seq = [ seq[0] ] + outSeq
        self.assertEqual(seq[1], [ 'wordlike', u'argv' ])
        
        print "result seq=", "\n".join(pytorqy.treeseq.seq_pretty(seq))
        
    def test7th(self):
        searchWordLike = r'~(word <- ("_", *("_" | r"^[a-zA-Z]" | r"^\d") | r"^[a-zA-Z]", *("_" | r"^[a-zA-Z]" | r"^\d")));'
        searchIdMake = r'~(id <- <>word);'
        
        exprs = compile_exprs([ searchWordLike, searchIdMake ])
        assert len(exprs) == 2

        inputText = r'argv[0];'
        inputText = inputText.decode(sys.getfilesystemencoding())
        seq = [ 'code' ]; seq.extend(split_to_strings_iter(inputText))
        
        for expr in exprs:
            posDelta, outSeq, dropSeq = expr.match(seq, 1)
            self.assertEqual(1 + posDelta, len(seq))
            seq = [ seq[0] ] + outSeq
        
        print "result seq=", "\n".join(pytorqy.treeseq.seq_pretty(seq))

    def test8th(self):
        searchFloatingPointLitearal = r"""~(
            l_float <- "0", (
                ri"^x[a-f0-9]+p\d+$" | ri"^x[a-f0-9]+p$", ("-" | "+"), r"^\d"
                | ri"^x[a-f0-9]+$", ".", *(ri"^[a-f0-9]+$" | r"^\d"), ?(ri"^[a-f0-9]*p\d+$" | ri"^[a-f0-9]*p$", ("-" | "+"), r"^\d")
            ), ?i"l"
        );
        """
        exprs = compile_exprs([ searchFloatingPointLitearal ])
        assert len(exprs) == 1
        
        pat = re.compile(r"\d+|[a-zA-Z_][a-zA-Z_0-9]*|[ \t]+|\r\n|.", re.DOTALL | re.IGNORECASE)
        
        sampleFlotingPointLiterals = [ '0x012abc.def', '0xabc.012', '0xap10' ]
        for inputText in sampleFlotingPointLiterals:
            inputText = inputText.decode(sys.getfilesystemencoding())
            seq = [ 'code' ]; seq.extend(split_to_strings_iter(inputText, pat))
            
            posDelta, outSeq, dropSeq = exprs[0].match(seq, 1)
            self.assertEqual(1 + posDelta, len(seq))
            seq = [ seq[0] ] + outSeq
            self.assertEqual(seq[0], 'code')
            self.assertEqual(seq[1][0], 'l_float')
            self.assertEqual(u"".join(seq[1][1:]), inputText)
        
if __name__ == '__main__':
    unittest.main()
