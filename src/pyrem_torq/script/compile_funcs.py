from __future__ import with_statement
from contextlib import contextmanager

import string

import pyrem_torq.expression as _pte
from pyrem_torq.treeseq import seq_pretty
from pyrem_torq.utility import split_to_strings_iter
import pyrem_torq.extra.expression_shortname as _pthes

# Priority of operators
# ()
# + ? * <> ~ @ req req^ any^
# ,
# |
# <- ::

# reserved words
# any any_node req

_newLineExpr = _pte.LiteralClass(['\r', '\n', '\r\n'])

def __fill(itemExpr, errorMessage):
    return [0,]*itemExpr + (_pte.EndOfNode() | _pte.ErrorExpr(errorMessage))

class CompileError(StandardError):
    def __init__(self, message, referenceNode):
        StandardError.__init__(self, message)
        self.referenceNode = referenceNode

def parse_to_ast(input, verboseOutput=None):
    A, AN, BtN, IN, L, LC, M, N, NM, R, XtA = _pthes.A, _pthes.AN, _pthes.BtN, _pthes.IN, _pthes.L, _pthes.LC, _pthes.M, _pthes.N, _pthes.NM, _pthes.R, _pthes.XtA
    
    seq = []
    if verboseOutput:
        @contextmanager
        def verbose_print_step_title_and_result_seq(title):
            verboseOutput.write(title)
            try: yield
            finally:
                verboseOutput.write("\n".join(seq_pretty(seq))); verboseOutput.write("\n")
    else:
        @contextmanager
        def verbose_print_step_title_and_result_seq(title):
            yield
    
    with verbose_print_step_title_and_result_seq('input'):
        s = [ 'code' ]; s.extend(split_to_strings_iter(input))
        seq[:] = s
    
    with verbose_print_step_title_and_result_seq('ParseToken'):
        def parseTokenExpr():
            def rst(label, *strings):
                assert len(strings) >= 1
                e = L(strings[0])
                for s in strings[1:]: e = e + L(s)
                return BtN(label, e)
            tokenExpr = _pte.Or.build(
                # spaces/comments
                _pte.Drop(BtN("space", [1,]*R(r"^\s$"))),
                _pte.Drop(BtN("comment", L('#') + [0,]*XtA(LC(["\n", "\r", "\r\n"])))),
                
                # operators
                rst("insert_subtree", "<", "-"),
                rst('null', 'null'),
                rst("comma", ","), rst("semicolon", ";"),
                rst("matches", ":", ":"), rst("anybut", "any", "^"), rst("reqbut", "req", "^"),
                rst("LP", "("), rst("RP", ")"), 
                rst("plus", "+"), rst("ques", "?"), rst("star", "*"), rst("or", "|"), rst("diamond", "<", ">"),
                rst("search", "~"),
                
                # string literal
                BtN("string_literal", [0,1]*LC([ 'i', 'ir', 'r', 'ri' ]) + L('"') + [0,]*(
                    L('\\') + XtA(LC([ '\t', '\n', '\r', '\f', '\v' ])) | \
                    XtA(LC([ '"', '\t', '\n', '\r', '\f', '\v' ]))
                ) + L('"')),
                L('"') + _pte.ErrorExpr('Invalid string literal'),
                
                # identifier (or reserved word)
                BtN("id", L('_') + [0,]*(L('_') | R(r"^[a-zA-Z]") | R(r"^[0-9]")) | 
                        R(r"^[a-zA-Z]") + [0,]*(L('_') | R(r"^[a-zA-Z]") | R(r"^[0-9]"))),
                
                # marker
                BtN('marker', 
                    _pte.Drop(BtN('markerop', L('@'))) + [0,]*(L('_') | R(r"^[a-zA-Z]") | R(r"^[0-9]")))
                    | L('@') + _pte.ErrorExpr('Invalid marker name')
            )
            return __fill(tokenExpr, "Can't extract a token")
        seq[:] = parseTokenExpr().parse(seq)
    
    with verbose_print_step_title_and_result_seq('parseReservedWords'):
        def parseReservedWordsExpr():
            def rw(name): return NM('id', L(name), newLabel=name) # reserved word
            reservedWordExpr = rw('req') | rw('error') | rw('any') | rw('any_node') | rw('null')
            return _pte.Search(reservedWordExpr)
        seq[:] = parseReservedWordsExpr().parse(seq)
    
    with verbose_print_step_title_and_result_seq('preChecking'):
        def parsePreCheckingExpr():
            idOrStr = N('id') | N('string_literal')
            preCheckExpr = _pte.Or.build(
                idOrStr + idOrStr + _pte.ErrorExpr("expected ',' between two ids/string literals"),
                N('RP') + idOrStr + _pte.ErrorExpr("expected ',' after paren"),
                idOrStr + N('LP') + _pte.ErrorExpr("expected ',' before paren (or misspelled built-in operator?)"),
                N('RP') + N('LP') + _pte.ErrorExpr("expected ',' after closing paren, before opening paren"),
                N('semicolon') + N('semicolon') + _pte.ErrorExpr("';' appears just after ';'"),
                L('^') + _pte.ErrorExpr("unexpected '^' (or misspelling of 'any^' or 'req^'?)"),
            )
            return _pte.Search(preCheckExpr)
        seq[:] = parsePreCheckingExpr().parse(seq)
    
    with verbose_print_step_title_and_result_seq('parseParen'):
        def parseParenExpr():
            ed = _pte.ExprDict()
            parenExpr = ed["parenExpr"] = XtA((N('LP') | N('RP'))) \
                | BtN('apply', IN('insert_subtree') + _pte.Drop(N('LP')) + (N('id') | N('null')) + _pte.Drop(N('insert_subtree')) + _pte.Drop(N('RP'))) \
                | BtN('param',  _pte.Drop(N('LP')) + [0,]*M("parenExpr") + _pte.Drop(N('RP')))
            return __fill(parenExpr, "Can't parse parens")
        seq[:] = parseParenExpr().parse(seq)
    
    def recurseApplyAndParam(marker): return NM('apply', A() + [0,]*marker) | NM('param', [0,]*marker)
    
    with verbose_print_step_title_and_result_seq('parseParen'):
        def parseUnaryOperatorsExpr():
            ed = _pte.ExprDict()
            unaryOperatorExpr = ed["unaryOperatorExpr"] = _pte.Or.build(recurseApplyAndParam(M("unaryOperatorExpr")),
                BtN('apply', (N("plus") | N("ques") | N("star") | N('search') | N('reqbut') | N('req') | N('anybut')) + M("unaryOperatorExpr")),
                BtN('error', _pte.Drop(N('error')) + N('string_literal', newLabel=_pte.FLATTEN)),
                BtN('error', _pte.Drop(N('error')) + \
                    NM('param', N('string_literal', newLabel=_pte.FLATTEN), newLabel=_pte.FLATTEN)),
                N('diamond') + N('id') + N('matches'), # special form
                BtN('apply', IN("expand") + _pte.Drop(N('diamond')) + N('id')),
                N('diamond') + _pte.ErrorExpr('operator <> only applicable to a node'),
                A())
            return _pte.Search(unaryOperatorExpr)
        seq[:] = parseUnaryOperatorsExpr().parse(seq)
    
    with verbose_print_step_title_and_result_seq('parseBinaryOperatorSeq'):
        def parseBinaryOperatorSeqExpr():
            ed = _pte.ExprDict()
            term = ed["term"] = recurseApplyAndParam(M("seqExpr")) | XtA(N('comma'))
            seqExpr = ed["seqExpr"] = BtN('apply', IN('seq') + term + [1,]*(_pte.Drop(N('comma')) + term)) \
                | term
            return __fill(seqExpr, "Can't parse binary operator Seq (,)")
        seq[:] = parseBinaryOperatorSeqExpr().parse(seq)
    
    with verbose_print_step_title_and_result_seq('parseBinaryOperatorOr'):
        def parseBinaryOperatorOrExpr():
            ed = _pte.ExprDict()
            term = ed["term"] = recurseApplyAndParam(M("orExpr")) | XtA(N('or'))
            orExpr = ed["orExpr"] = BtN('apply', 
                IN('or') + term + [1,]*(_pte.Drop(N('or')) + term)) \
                | term
            return __fill(orExpr, "Can't parse binary operator Or (|)")
        seq[:] = parseBinaryOperatorOrExpr().parse(seq)
    
    with verbose_print_step_title_and_result_seq('parseBinaryOperatorMatch'):
        def parseBinaryOperatorMatchExpr():
            ed = _pte.ExprDict()
            def aop(opName): return BtN('apply', IN(opName) + N('id') + _pte.Drop(N(opName)) + M("matchExpr"))
            def aopwd(opName): return BtN('apply', IN(opName) + IN('expand') + _pte.Drop(N('diamond')) + N('id') + _pte.Drop(N(opName)) + M("matchExpr"))
            term = ed["term"] = recurseApplyAndParam(M("matchExpr")) | XtA((N('matches') | N('assign_subtree')))
            matchExpr = ed["matchExpr"] = aopwd('matches') | \
                BtN('apply', IN('matches') + N('id') + _pte.Drop(N('matches')) + M("matchExpr")) | \
                BtN('apply', IN('insert_subtree') + (N('id') | N('null')) + _pte.Drop(N('insert_subtree')) + M("matchExpr")) | \
                term
            return __fill(matchExpr, "Can't parse binary operator match (::)")
        seq[:] = parseBinaryOperatorMatchExpr().parse(seq)
        
    with verbose_print_step_title_and_result_seq('parseReduceRedundantParen'):
        def parseReduceRedundantParenExpr():
            ed = _pte.ExprDict()
            term = ed["term"] = NM('apply', A() + [0,]*M("paramExpr")) | XtA(N('param'))
            paramExpr = ed["paramExpr"] = NM('param', M("paramExpr"), newLabel=_pte.FLATTEN) \
                | NM('param', AN()) \
                | term
            return __fill(paramExpr, "Can't parse redundant paren")
        seq[:] = parseReduceRedundantParenExpr().parse(seq)
    
    with verbose_print_step_title_and_result_seq('parseStatements'):
        def parseStatementsExpr():
            statementExpr = BtN('statement', XtA(N('semicolon')) + N('semicolon'))
            return __fill(statementExpr, "Can't parse statement")
        seq[:] = parseStatementsExpr().parse(seq)
    
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

def __unescape(s):
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
    return "".join(parts)
    
def convert_literal_to_expression_object(s):
    s0 = s
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
        return _pte.Rex(s, ignoreCase=ignoreCase)
    elif ignoreCase:
        for c in s:
            if c not in string.ascii_letters:
                raise IgnoreCaseForNonAlphabetChar(s0)
        if len(s) != 1:
            return _pte.Rex("^" + s + "$", ignoreCase=True)
        else:
            return _pte.LiteralClass([ s.lower(), s.upper() ])
    else:
        return _pte.Literal(__unescape(s))

def convert_to_expression_object(seq, replaces=None):
    if replaces:
        if isinstance(replaces, ( list, tuple )):
            assert len(replaces) == 2
            assert isinstance(replaces[1], _pte.TorqExpression)
            replaceTable = { replaces[0]:replaces[1] }
        else:
            for label, expr in replaces.iteritems():
                assert isinstance(expr, _pte.TorqExpression)
            replaceTable = replaces
    else:
        replaceTable = {}
    
    def nodeNameIn(seq, names): 
        return len(seq) >= 1 and seq[0] in names
    alpha_Set = frozenset(list(string.ascii_letters) + [ '_' ])
    alnum_Set = frozenset(list(string.ascii_letters) + [ '_' ] + list(string.digits))
    def marker2Label(seq):
        assert seq[0] == 'marker'
        assert len(seq) >= 2
        if len(seq) == 2 and seq[1] in ("req", "reqbut", 'null', 'any', 'any_node', 'error'):
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
    
    nameToRep = { 'ques': _pte.Repeat.ZeroOrOne, 'star': _pte.Repeat.ZeroOrMore, 'plus': _pte.Repeat.OneOrMore }
    nameToOrSeq = { 'or': _pte.Or.build, 'seq': _pte.Seq.build }
    #nameToOrSeq = { 'or': OrExpr, 'seq': SeqExpr }
    nameToBuiltinFunc = { 'req': _pte.Req.build, 'reqbut': _pte.Xcp.build, 'anybut': _pte.XcpThenAny.build, 'search' : _pte.Search.build }
    
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
                return _pte.NodeMatch(label, cnv_i(seq[3]), newLabel=(_pte.FLATTEN if is_flatten else None))
            elif seq1NodeName == 'insert_subtree':
                if len_seq == 3:
                    if seq[2][0] == 'null': raise CompileError("Invalid form. '(null <- )' is not permitted")
                    label = id2Label(seq[2])
                    if not label: raise CompileError("InsertNode(<-) requires an identifier", seq[2])
                    return _pte.InsertNode(label)
                else:
                    if len_seq != 4: raise CompileError("Invalid InsertNode(<-)", seq1)
                    if seq[2][0] == 'null':
                        return _pte.Drop(cnv_i(seq[3]))
                    else:
                        label = id2Label(seq[2])
                        if not label: raise CompileError("InsertNode(<-) requires an identifier", seq[2])
                        return _pte.BuildToNode(label, cnv_i(seq[3]))
            elif seq1NodeName == 'insert':
                if len_seq != 3: raise CompileError("Invalid insert expr", seq1)
                label = id2Label(seq[2])
                if not label: raise CompileError("insert requires an identifier", seq[2])
                return _pte.InsertNode(label)
            elif seq1NodeName == 'expand':
                if len_seq != 3: raise CompileError("Invalid flatten(<>) expr", seq1)
                label = id2Label(seq[2])
                if not label: raise CompileError("Operator flatten(<>) requires an identifier", seq[2])
                return _pte.Node(label, newLabel=_pte.FLATTEN)
            elif seq1NodeName in nameToBuiltinFunc:
                if len_seq != 3: raise CompileError("Invalid req/req^/any^ expr", seq1)
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
        elif seq0 == "any":
            assert len_seq == 2
            return _pte.Any()
        elif seq0 == "any_node":
            assert len_seq == 2
            return _pte.AnyNode()
        elif seq0 == 'id':
            label = id2Label(seq)
            if not label: raise CompileError("Invalid Label", seq0)
            return _pte.Node(label)
        elif seq0 == 'marker':
            label = marker2Label(seq)
            if not label: raise CompileError("Invalid Marker", seq0)
            r = replaceTable.get(label)
            if r is not None:
                return r
            return _pte.Marker(label)
        elif seq0 == 'error':
            if not(len_seq >= 2): raise CompileError("Empty error message", seq0)
            s = "".join(seq[1:])
            return _pte.ErrorExpr(__unescape(s))
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

def compile(src, recursionAtMarker0=True, replaces=None, topLevelSplit=False):
    try:
        seq = parse_to_ast(src)
    except _pte.InterpretError, e:
        raise CompileError("pos %s: error: %s" % ( repr(e.stack), str(e) ), None)
    
    exprs = convert_to_expression_object(seq, replaces=replaces)
    
    if recursionAtMarker0:
        for expr in exprs:
            _pte.assign_marker_expr(expr, "0", expr)
    
    if topLevelSplit:
        return exprs
    
    return _pte.Or(*exprs)
