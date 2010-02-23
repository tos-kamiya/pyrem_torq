import string

from pytorqy.expression import *
from pytorqy.expression_shortname import *
from pytorqy.treeseq import seq_pretty
from pytorqy.utility import split_to_strings_iter

# Priority of operators
# ()
# + ? * <> ~ @ xcp req any^
# ,
# |
# <- ::

_newLineExpr = LC(['\r', '\n', '\r\n'])

def __parse(seq, itemExpr, errorMessage):
    searchExpr = [0,]*itemExpr + (EndOfNode() | ErrorExpr(errorMessage))
    posDelta, outSeq, dropSeq = searchExpr.match(seq, 1)
    assert 1 + posDelta == len(seq) 
    return [ seq[0] ] + outSeq

class CompileError(StandardError):
    def __init__(self, message, referenceNode):
        StandardError.__init__(self, message)
        self.referenceNode = referenceNode

def parse_to_ast(s, verboseOutput=None):
    if verboseOutput:
        def verbosePrintTitle(title): verboseOutput.write("> %s\n" % title)
        def verbosePrintSeq(seq): verboseOutput.write("\n".join(seq_pretty(seq))); verboseOutput.write("\n")
    else:
        def verbosePrintTitle(title): pass
        def verbosePrintSeq(seq): pass
    
    verbosePrintTitle('input')
    seq = [ 'code' ]; seq.extend(split_to_strings_iter(s))
    verbosePrintSeq(seq)    
    
    verbosePrintTitle('ParseToken')
    def parseToken(seq):
        def rst(label, *strings):
            assert len(strings) >= 1
            e = L(strings[0])
            for s in strings[1:]: e = e + L(s)
            return BtN(label, e)
        tokenExpr = Or(
            # spaces/comments
            Drop(BtN("space", [1,]*R(r"^\s$"))),
            Drop(BtN("comment", L('#') + [0,]*XtA(LC(["\n", "\r", "\r\n"])))),
            
            # operators
            rst("insert_subtree", "<", "-"),
            rst("comma", ","), rst("semicolon", ";"),
            rst("matches", ":", ":"), rst("anybut", "any", "^"),
            rst("LP", "("), rst("RP", ")"), 
            rst("plus", "+"), rst("ques", "?"), rst("star", "*"), rst("or", "|"), rst("diamond", "<", ">"),
            rst("search", "~"),
            
            # string literal
            BtN("string_literal", [0,1]*LC([ 'i', 'ir', 'r', 'ri' ]) + L('"') + [0,]*(
                L('\\') + XtA(LC([ '\t', '\n', '\r', '\f', '\v' ])) | \
                XtA(LC([ '"', '\t', '\n', '\r', '\f', '\v' ]))
            ) + L('"')),
            L('"') + ErrorExpr('Invalid string literal'),
            
            # identifier (or reserved word)
            BtN("id", L('_') + [0,]*(L('_') | R(r"^[a-zA-Z]") | R(r"^[0-9]")) | 
                    R(r"^[a-zA-Z]") + [0,]*(L('_') | R(r"^[a-zA-Z]") | R(r"^[0-9]"))),
            
            # marker
            BtN('marker', 
                Drop(BtN('markerop', L('@'))) + [0,]*(L('_') | R(r"^[a-zA-Z]") | R(r"^[0-9]")))
                | L('@') + ErrorExpr('Invalid marker name')
        )
        return __parse(seq, tokenExpr, "Can't extract a token")
    seq = parseToken(seq)
    verbosePrintSeq(seq)    
    
    verbosePrintTitle('parseReservedWords')
    def parseReservedWords(seq):
        def rw(name): return NM('id', L(name), newLabel=name) # reserved word
        reservedWordExpr = rw('req') | rw('xcp') 
        return __parse(seq, reservedWordExpr | A(), "Can't parse reserved words")
    seq = parseReservedWords(seq)
    verbosePrintSeq(seq)    
    
    verbosePrintTitle('preChecking')
    def parsePreChecking(seq):
        idOrStr = N('id') | N('string_literal')
        preCheckExpr = idOrStr + idOrStr + ErrorExpr("use ',' operator for Seq expr") \
            | N('RP') + N('id') + ErrorExpr("expected ',' after paren") \
            | N('id') + N('LP') + ErrorExpr("expected req or xcp before paren")
        preCheckExpr = preCheckExpr | A()
        return __parse(seq, preCheckExpr, "Can't parse pre-checking")
    seq = parsePreChecking(seq)
    verbosePrintSeq(seq)    
    
    verbosePrintTitle('parseParen')
    def parseParen(seq):
        ed = ExprDict()
        parenExpr = ed["parenExpr"] = XtA((N('LP') | N('RP'))) \
            | BtN('apply', IN('insert_subtree') + Drop(N('LP')) + N('id') + Drop(N('insert_subtree')) + Drop(N('RP'))) \
            | BtN('param',  Drop(N('LP')) + [0,]*M("parenExpr") + Drop(N('RP')))
        return __parse(seq, parenExpr, "Can't parse parens")
    seq = parseParen(seq)
    verbosePrintSeq(seq)    
    
    def recurseApplyAndParam(marker): return NM('apply', A() + [0,]*marker) | NM('param', [0,]*marker)
    
    verbosePrintTitle('parseUnaryOperators')
    def parseUnaryOperators(seq):
        ed = ExprDict()
        unaryOperatorExpr = ed["unaryOperatorExpr"] = Or(recurseApplyAndParam(M("unaryOperatorExpr")),
            BtN('apply', (N("plus") | N("ques") | N("star") | N('search') | N('xcp') | N('req') | N('anybut')) + M("unaryOperatorExpr")),
            N('diamond') + N('id') + N('matches'), # special form
            BtN('apply', IN("expand") + Drop(N('diamond')) + N('id')),
            N('diamond') + ErrorExpr('operator <> only applicable to a node'),
            A())
        return __parse(seq, unaryOperatorExpr, "Can't parse unary operators")
    seq = parseUnaryOperators(seq)
    verbosePrintSeq(seq)    
    
    verbosePrintTitle('parseBinaryOperatorSeq')
    def parseBinaryOperatorSeq(seq):
        ed = ExprDict()
        term = ed["term"] = recurseApplyAndParam(M("seqExpr")) | XtA(N('comma'))
        seqExpr = ed["seqExpr"] = BtN('apply', IN('seq') + term + [1,]*(Drop(N('comma')) + term)) \
            | term
        return __parse(seq, seqExpr, "Can't parse binary operator SEQ")
    seq = parseBinaryOperatorSeq(seq)
    verbosePrintSeq(seq)    
    
    verbosePrintTitle('parseBinaryOperatorOr')
    def parseBinaryOperatorOr(seq):
        ed = ExprDict()
        term = ed["term"] = recurseApplyAndParam(M("orExpr")) | XtA(N('or'))
        orExpr = ed["orExpr"] = BtN('apply', IN('or') + term + [1,]*(Drop(N('or')) + term)) \
            | term
        return __parse(seq, orExpr, "Can't parse binary operator OR")
    seq = parseBinaryOperatorOr(seq)
    verbosePrintSeq(seq)    
    
    verbosePrintTitle('parseBinaryOperatorAssign')
    def parseBinaryOperatorAssign(seq):
        ed = ExprDict()
        def aop(opName): return BtN('apply', IN(opName) + N('id') + Drop(N(opName)) + M("assignExpr"))
        def aopwd(opName): return BtN('apply', IN(opName) + IN('expand') + Drop(N('diamond')) + N('id') + Drop(N(opName)) + M("assignExpr"))
        term = ed["term"] = recurseApplyAndParam(M("assignExpr")) | XtA((N('matches') | N('assign_subtree')))
        assignExpr = ed["assignExpr"] = aopwd('matches') | aop('matches') | aop('insert_subtree') | term
        return __parse(seq, assignExpr, "Can't parse binary operator ASSIGN")
    seq = parseBinaryOperatorAssign(seq)
    verbosePrintSeq(seq)    
    
    verbosePrintTitle('parseReduceRedundantParen')
    def parseReduceRedundantParen(seq):
        ed = ExprDict()
        term = ed["term"] = NM('apply', A() + [0,]*M("paramExpr")) | XtA(N('param'))
        paramExpr = ed["paramExpr"] = NM('param', M("paramExpr"), newLabel=FLATTEN) \
            | NM('param', AN()) \
            | term
        return __parse(seq, paramExpr, "Can't parse redundant paren")
    seq = parseReduceRedundantParen(seq)
    verbosePrintSeq(seq)    
    
    verbosePrintTitle('parseStatements')
    def parseStatements(seq):
        statementExpr = BtN('statement', XtA(N('semicolon')) + N('semicolon'))
        return __parse(seq, statementExpr, "Can't parse statement")
    seq = parseStatements(seq)
    verbosePrintSeq(seq)    
    
    #print "\n".join(seq_pretty(seq))
    return seq

class InvalidLiteral(ValueError): pass
class InvalidBackquote(InvalidLiteral): pass
class InvalidBackquoteSurrogatePairNotSupportedYet(InvalidBackquote): pass
class IgnoreCaseForNonAlphabetChar(ValueError): pass

__specials = { 'a':"\a", 'b':"\b", 'f':"\f", 'n':"\n", 'r':"\r", 't':"\t", 'v':"\v" }

def eval_backquote_str(s):
    assert s[0] == '\\'
    if len(s) == 1:
        raise InvalidBackquote
    c = s[1]
    if c == '\\':
        return '\\', 2
    elif c in ("\'", "\""):
        return c, 2
    elif c in __specials:
        return __specials[c], 2
    elif c == 'u':
        assert len(s) >= 2 + 4
        codePoint = int(s[2:2+4], 16)
        if 0xd800 <= codePoint <= 0xdfff:
            raise InvalidBackquoteSurrogatePairNotSupportedYet
        return unichr(codePoint), 2 + 4
    elif c == 'U':
        assert len(s) >= 2 + 8
        codePoint = int(s[2:2+8], 16)
        return unichr(codePoint), 2 + 8
    elif c == 'x':
        assert len(s) >= 2 + 2
        codePoint = int(s[2:2+2], 16)
        return chr(codePoint), 2 + 2
    else:
        raise InvalidBackquote
    
def convert_literal_to_expression_object(s0):
    s = s0
    
    ignoreCase = False
    regex = False
    if s[0:2] in ('ir', 'ri'):
        ignoreCase = True
        regex = True
        s = s[2:]
    elif s[0:1] == 'i':
        ignoreCase = True
        s = s[1:]
    elif s[0:1] == 'r':
        regex = True
        s = s[1:]
        
    assert s # is not empty
    assert s[0] == '\"'
    assert s[-1] == '\"'
    s = s[1:-1]
    
    if regex:
        return R(s, ignoreCase=ignoreCase)
    elif ignoreCase:
        for c in s:
            if c not in string.ascii_letters:
                raise IgnoreCaseForNonAlphabetChar(s0)
        if len(s) != 1:
            return R("^" + s + "$", ignoreCase=True)
        else:
            return LC([ s.lower(), s.upper() ])
    else:
        parts = []
        i = 0
        len_s = len(s)
        while i < len_s:
            bi = s.find('\\', i)
            if bi >= 0:
                if bi != 0: parts.append(s[i:bi])
                value, j = eval_backquote_str(s[bi:])
                parts.append(value)
                i = bi + j
            else:
                parts.append(s[i:])
                i = len_s
        evaledS = "".join(parts)
        return L(evaledS)

def convert_to_expression_object(seq):
    def nodeNameIn(seq, names): 
        return len(seq) >= 1 and seq[0] in names
    alpha_Set = frozenset(list(string.ascii_letters) + [ '_' ])
    alnum_Set = frozenset(list(string.ascii_letters) + [ '_' ] + list(string.digits))
    def marker2Label(seq):
        assert seq[0] == 'marker'
        assert len(seq) >= 2
        if len(seq) == 2 and seq[1] in ("req", "xcp", "null", "any"):
            return None
        return "".join(seq[1:])
    def id2Label(seq):
        if not(len(seq) >= 2): return None
        if seq[0] != 'id': return None
        s = seq[1:]
        if s[0][0] not in alpha_Set: return None
        for ss in s[1:]:
            if ss[0] not in alnum_Set: return None
        return "".join(s)
    
    assert len(seq) >= 1 and seq[0] == 'code'
    
    nameToRep = { 'ques': Repeat.ZeroOrOne, 'star': Repeat.ZeroOrMore, 'plus': Repeat.OneOrMore }
    nameToOrSeq = { 'or': Or.build, 'seq': Seq.build }
    #nameToOrSeq = { 'or': OrExpr, 'seq': SeqExpr }
    nameToBuiltinFunc = { 'req': Req.build, 'xcp': Xcp.build, 'anybut': XcpThenAny.build, 'search' : Search.build }
    
    literalExprPool = {}
    
    def cnv_i(seq):
        len_seq = len(seq)
        
        assert len_seq >= 1
        if len_seq == 1: raise CompileError("Invalid Code", seq)
        seq0, seq1 = seq[0], seq[1]
        if seq0 == 'apply':
            seq1NodeName = seq1[0] if len(seq1) >= 1 else None
            if seq1NodeName == 'matches':
                is_flatten = False
                if nodeNameIn(seq[2], ( 'expand', )):
                    is_flatten = True
                    del seq[2]; len_seq = len(seq)
                if len_seq != 4: raise CompileError("Invalid NodeMatch(::) expr", seq1)
                label = id2Label(seq[2])
                if not label: raise CompileError("Operator NodeMatch(::) requires an identifier", seq[2])
                return NM(label, cnv_i(seq[3]), newLabel=(FLATTEN if is_flatten else None))
            elif seq1NodeName == 'insert_subtree':
                if len_seq == 3:
                    label = id2Label(seq[2])
                    if not label: raise CompileError("InsertNode(<-) requires an identifier", seq[2])
                    if label == 'null': raise CompileError("Invalid form. '(null <- )' is not permitted")
                    else:
                        return IN(label)
                else:
                    if len_seq != 4: raise CompileError("Invalid InsertNode(<-)", seq1)
                    label = id2Label(seq[2])
                    if not label: raise CompileError("InsertNode(<-) requires an identifier", seq[2])
                    if label == 'null':
                        return Drop(cnv_i(seq[3]))
                    else:
                        return BtN(label, cnv_i(seq[3]))
            elif seq1NodeName == 'insert':
                if len_seq != 3: raise CompileError("Invalid insert expr", seq1)
                label = id2Label(seq[2])
                if not label: raise CompileError("insert requires an identifier", seq[2])
                return IN(label)
            elif seq1NodeName == 'expand':
                if len_seq != 3: raise CompileError("Invalid flatten(<>) expr", seq1)
                label = id2Label(seq[2])
                if not label: raise CompileError("Operator flatten(<>) requires an identifier", seq[2])
                return N(label, newLabel=FLATTEN)
            elif seq1NodeName in nameToBuiltinFunc:
                if len_seq != 3: raise CompileError("Invalid req/xcp/any^ expr", seq1)
                r = cnv_i(seq[2])
                return nameToBuiltinFunc[seq1[0]](r)
            elif seq1NodeName in nameToRep:
                if len_seq != 3: raise CompileError("Invalid Repeat expr", seq1)
                r = cnv_i(seq[2])
                return nameToRep[seq1[0]](r)
            elif seq1NodeName in nameToOrSeq:
                if not(len_seq >= 2): raise CompileError("Invalid Or(|)/Seq(,) expr", seq1)
                r = [ cnv_i(item) for item in seq[2:] ]
                return nameToOrSeq[seq1[0]](*r)
            else:
                assert False
        elif seq0 == 'id':
            label = id2Label(seq)
            if not label: raise CompileError("Invalid Label", seq0)
            if label == 'any':
                return A()
            else:
                return N(label)
        elif seq0 == 'marker':
            label = marker2Label(seq)
            if not label: raise CompileError("Invalid Marker", seq0)
            return Marker(label)
        elif seq0 == 'string_literal':
            if not(len_seq >= 2): raise CompileError("Empty Literal", seq0)
            s = "".join(seq[1:])
            pooledExpr = literalExprPool.get(s)
            if not pooledExpr:
                try:
                    pooledExpr = convert_literal_to_expression_object(s)
                    literalExprPool[s] = pooledExpr
                except AssertionError:
                    raise CompileError("Invalid literal", seq0)
            return pooledExpr
        else:
            raise CompileError("Invalid Token", seq)
        
    r = []
    for statementSeq in seq[1:]:
        assert len(statementSeq) >= 1
        if statementSeq[0] != 'statement':
            raise CompileError("Expected Statement", statementSeq)
        if not(len(statementSeq) == 3 and nodeNameIn(statementSeq[2], ( 'semicolon' ))):
            raise CompileError("Invalid Statement", statementSeq)
        r.append(cnv_i(statementSeq[1]))
    
    return r

def compile(src, recursionAtMarker0=True):
    try:
        seq = parse_to_ast(src)
    except InterpretError as e:
        raise CompileError("pos %s: error: %s" % ( repr(e.stack), str(e) ), None)
    
    exprs = convert_to_expression_object(seq)
    
    if recursionAtMarker0:
        for expr in exprs:
            assign_marker_expr(expr, "0", expr)
        
    return exprs

if __name__ == '__main__':
    #s = 'text match= "{";'
    #s = 'text match= (LB <- "{") , (RB <- "}") | ?insert(hoge) huga;'
    s = 'text match= (LBRB <- "{", "}") | ?insert(hoge);'
    #s = 'text match= *r"^[0-9]";'
    exprs = compile(s)
    print "exprs=", exprs
