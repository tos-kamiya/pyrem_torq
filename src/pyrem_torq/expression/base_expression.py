from itertools import chain as _chain
        
def inner_expr_iter(expr):
    visitedExprIDSet = set()
    def iei_i(e):
        ide = id(e)
        if ide in visitedExprIDSet: return # prevent infinite recursion
        
        visitedExprIDSet.add(ide)
        if hasattr(e, "extract_exprs"):
            for item in e.extract_exprs():
                if item is not None:
                    yield item
                    for v in iei_i(item): yield v # need PEP380
    return iei_i(expr)

class InvalidRepetitionCount(ValueError): pass

class MatchCandidateForLookAhead:
    def __init__(self, nodes=[], literals=[], emptyseq=False):
        """ MatchCandidateForLookAhead(nodes=[], literals=[], emptyseq=False).
            nodes are the labels that an expression may match to.
            when nodes=None, it means that an expression may match any labeled nodes.
            literals are the strings that an expression may match to.
            when literals=None, it means that an expression may match any strings.
            emptyseq specifies an expression may match to an empty seq or not.
        """
        if nodes is None:
            self.__nodes = None
        else:
            assert None not in nodes
            self.__nodes = tuple(sorted(set(nodes)))
        if literals is None:
            self.__literals = None
        else:
            assert None not in literals
            self.__literals = tuple(sorted(set(literals)))
        self.__emptyseq = not not emptyseq
    
    def _getnodes(self): return self.__nodes
    def _getliterals(self): return self.__literals
    def _getemptyseq(self): return self.__emptyseq
    
    nodes = property(_getnodes)
    literals = property(_getliterals)
    emptyseq = property(_getemptyseq)

    def __eq__(self, right): 
        return right.__class__ == MatchCandidateForLookAhead and \
            self.__nodes == right.__nodes and self.__literals == right.__literals and self.__emptyseq == right.__emptyseq

    def __repr__(self): 
        return "MatchCandiateForLookAhead(nodes=%s,literals=%s,emptyseq=%s)" % ( repr(self.__nodes), repr(self.__literals), repr(self.__emptyseq) )
        
    def __hash__(self):
        L = []
        L.extend(self.__nodes)
        L.extend(self.__literals)
        L.append(self.__emptyseq)
        return sum(map(hash, L))
    
_zeroLengthReturnValue = 0, ()

class TorqExpression(object):
    ''' A base class of torq expression classes. (Abstract class.) '''
    
    def __add__(self, other): return Seq(self, other)
    def __or__(self, other): return Or(self, other)
    
    def __rmul__(self, left):
        if isinstance(left, list):
            if len(left) == 1:
                if not isinstance(left[0], int): raise InvalidRepetitionCount("Invalid type for 1st value of repetition specifier")
                lower, upper = left[0], None
            else:
                if len(left) != 2: raise InvalidRepetitionCount("Invalid type for repetition specifier")
                if not isinstance(left[0], int): raise InvalidRepetitionCount("Invalid type for 1st value of repetition specifier")
                if not (left[1] is None or isinstance(left[1], int)): 
                    raise InvalidRepetitionCount("Invalid type for 2nd value of repetition specifier")
                lower, upper = left
        elif isinstance(left, int):
            lower = upper = left
        else:
            raise InvalidRepetitionCount("Invalid type for repeat specifier")
        assert upper is None or lower <= upper
        return Repeat(self, lower, upper)
            
    def match(self, inpSeq, inpPos):
        ''' Do matching of the expression and input sequence.
            If a substring inpSeq[inpPos:x] is matched by the expression (self),
            returns a tuple of (length of matching substring, list of output nodes).
            Otherwise, returns a tuple (0, []).
        '''
        
        assert inpPos >= 1
        len_inpSeq = len(inpSeq)
        assert inpSeq.__class__ is list and len_inpSeq >= 1
        if inpPos == len_inpSeq:
            r = self._match_eon(inpSeq, inpPos, None)
        else:
            lookAhead = inpSeq[inpPos]
            if lookAhead.__class__ is list:
                r = self._match_node(inpSeq, inpPos, lookAhead)
            else:
                #assert lookAhead.__class__ is int #debug
                r = self._match_lit(inpSeq, inpPos, ( lookAhead, inpSeq[inpPos + 1] ))
        if r is None: return 0, []
        p, o = r
        if o.__class__ is not list: o = list(o)
        return p, o
    
    def parse(self, inpSeq):
        ''' Do matching of the expression and input sequence.
            If the entire inpSeq is matched by the expression (self),
            returns list of output nodes.
            Otherwise, returns None.
        '''
        
        p, o = self.match(inpSeq, 1)
        if 1 + p != len(inpSeq): return None
        newSeq = [ inpSeq[0] ]; newSeq.extend(o)
        return newSeq
    
    def _match_node(self, inpSeq, inpPos, lookAhead): pass # return None
    _match_lit = _match_eon = _match_node
    
    def getMatchCandidateForLookAhead(self):
        # return a MatchCandidateForLookAhead object or None
        return None 
    
    @staticmethod
    def __call_extract_exprs_if_having(self):
        return list(self.extract_exprs()) if hasattr(self, "extract_exprs") else []
    
    def _eq_i(self, right, alreadyComparedExprs):
        selfId = id(self)
        
        rightIdWhenSelfIsFoundInComparedExprs = alreadyComparedExprs.get(selfId, None)
        if rightIdWhenSelfIsFoundInComparedExprs is not None:
            return id(right) == rightIdWhenSelfIsFoundInComparedExprs
        rightId = id(right)

        alreadyComparedExprs[selfId] = rightId
        if isinstance(right, self.__class__):
            ex = TorqExpression.__call_extract_exprs_if_having
            for es, er in zip(ex(self), ex(right)):
                if not es._eq_i(er, alreadyComparedExprs):
                    return False
            else:
                return True
        return False
    
    def __eq__(self, right): return self._eq_i(right, dict())
    
    def __repr__(self): 
        return "%s(%s)" % ( self.__class__.__name__, ",".join(map(repr, TorqExpression.__call_extract_exprs_if_having(self))) )
        
    def __hash__(self):
        return hash(self.__class__.__name__) + sum(hash(e) for e in TorqExpression.__call_extract_exprs_if_having(self))
    
    def optimized(self, objectpool={}): return self

class TorqExpressionWithExpr(TorqExpression):
    ''' (Abstract class.) intended to be used internally. '''

    __slots__ = [ '_expr', '_expr_match_node', '_expr_match_lit', '_expr_match_eon' ]
    
    def getexpr(self): return self._expr
    expr = property(getexpr)
    
    def _set_expr(self, expr):
        assert isinstance(expr, TorqExpression)
        self._expr = expr
    
    def extract_exprs(self): return [ self._expr ]

class TorqExpressionSingleton(TorqExpression):
    ''' (Abstract class.) intended to be used internally. '''
    __slots__ = [ ]
    
    def _eq_i(self, right, alreadyComparedExprs):
        return right.__class__ == self.__class__

    def optimized(self, objectpool={}):
        h = hash(self)
        for e in objectpool.get(h, []):
            if e.__class__ is self.__class__:
                return e
        objectpool.setdefault(h, []).append(self)
        return self
    
def _orflatener(exprs):
    for e in exprs:
        if e.__class__ is Or:
            for i in _orflatener(e.exprs): yield i # need PEP380
        else: yield e

class Or(TorqExpression):
    ''' Or expression matches a sequence, iff the sequence is matched by one of the internal expressions.
    '''
    
    __slots__ = [ '__exprs', '__ntbl_get', '_unknown_nlst', '__ltbl_get', '__unknown_llst', '__elst', '__mc4la' ]
    
    def __init__(self, *exprs):
        self._set_exprs(exprs)
    
    def getexprs(self): return self.__exprs
    exprs = property(getexprs)
    
    def _set_exprs(self, exprs):
        self.__exprs = exprs
        for expr in self.__exprs: assert isinstance(expr, TorqExpression)
        ntbl, self.__unknown_nlst, ltbl, self.__unknown_llst, self.__elst, including_unknown_req = Or._make_tables(self.__exprs)
        if including_unknown_req:
            self.__mc4la = None
        else:
            self.__mc4la = MatchCandidateForLookAhead(
                    nodes=None if self.__unknown_nlst else sorted(ntbl.iterkeys()),
                    literals=None if self.__unknown_llst else sorted(ltbl.iterkeys()),
                    emptyseq=not not self.__elst) 
        self.__ntbl_get = ntbl.get
        self.__ltbl_get = ltbl.get
    
    @staticmethod
    def _make_tables(exprs):
        def append_to_all_values(tbl, item):
            for L in tbl.itervalues(): L.append(item)
        includingUnknownReq = any(e is None for e in exprs)
        exprAndReqs = [( expr, expr.getMatchCandidateForLookAhead() ) for expr in exprs]
                    
        ns, ls = [], []
        for r in filter(None, (r for _, r in exprAndReqs)):
            if r.nodes is not None: ns.extend(r.nodes)
            if r.literals is not None: ls.extend(r.literals)
        
        ntbl = dict(( lbl, [] ) for lbl in ns)
        unknown_nlst = []
        ltbl = dict(( s, [] ) for s in ls)
        unknown_llst = []
        elst = []
        for expr, r in exprAndReqs:
            if r is not None:
                if r.nodes is not None:
                    for lbl in r.nodes: ntbl[lbl].append(expr)
                else:
                    append_to_all_values(ntbl, expr)
                    unknown_nlst.append(expr)
                if r.literals is not None:
                    for s in r.literals: ltbl[s].append(expr)
                else:
                    for L in ltbl.itervalues(): L.append(expr)
                    unknown_llst.append(expr)
                if r.emptyseq: elst.append(expr)
            else:
                for L in _chain(ntbl.itervalues(), ltbl.itervalues(), [ unknown_nlst, unknown_llst, elst ]):
                    L.append(expr)
        return ntbl, unknown_nlst, ltbl, unknown_llst, elst, includingUnknownReq
    
    def extract_exprs(self):
        return list(self.__exprs)
        
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        for expr in self.__ntbl_get(lookAheadNode[0], self.__unknown_nlst):
            r = expr._match_node(inpSeq, inpPos, lookAheadNode)
            if r is not None:
                return r
        #else: return None
        
    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        #assert len(lookAheadString) == 2
        for expr in self.__ltbl_get(lookAheadString[1], self.__unknown_llst):
            r = expr._match_lit(inpSeq, inpPos, lookAheadString)
            if r is not None:
                return r
        #else: return None
    
    def _match_eon(self, inpSeq, inpPos, lookAheadDummy):
        for expr in self.__elst:
            r = expr._match_eon(inpSeq, inpPos, lookAheadDummy)
            if r is not None:
                return r
        #else: return None

    def getMatchCandidateForLookAhead(self): 
        return self.__mc4la
            
    def optimized(self, objectpool={}):
        exprs = list(_orflatener(self.__exprs))
        if not exprs: return Never().optimized(objectpool)
        mergedExprs = [ exprs[0] ]
        for e in exprs[1:]:
            prev = mergedExprs[-1]
            m = prev.or_merged(e) if hasattr(prev, "or_merged") else None
            if m is not None:
                mergedExprs[-1] = m
            else:
                mergedExprs.append(e)
        return Never().optimized(objectpool) if not mergedExprs else \
                 mergedExprs[0] if len(mergedExprs) == 1 else \
                 Or(*mergedExprs)

def _seqflatener(exprs):
    for e in exprs:
        if e.__class__ is Seq:
            for i in _seqflatener(e.exprs): yield i # need PEP380
        else: yield e

class Seq(TorqExpression):
    ''' Seq expression matches a sequence, iff the sequence is a concatenation of the sequences, s1, s2, ...
    Here sequence s1 is matched by the 1st internal expression, s2 by 2nd, and so on.
    '''
    
    __slots__ = [ '__exprs', '__expr0', '__mc4la', ]
    
    def getexprs(self): return self.__exprs
    exprs = property(getexprs)
    
    def _set_exprs(self, exprs):
        self.__exprs = tuple(exprs)
        for expr in self.__exprs: assert isinstance(expr, TorqExpression)
        self.__expr0 = self.__exprs[0] if self.__exprs else Epsilon()
        
    def extract_exprs(self): return list(self.__exprs)
        
    def __init__(self, *exprs):
        self._set_exprs(exprs)
        self.__set_mc4la()
        
    def __set_mc4la(self):
        ns, ls = [], []
        acceptEmpty = True
        for r in (expr.getMatchCandidateForLookAhead() for expr in self.exprs):
            if r is None: 
                self.__mc4la = None
                return
            if ns is None or r.nodes is None:
                ns = None
            else:
                ns.extend(r.nodes)
            if ls is None or r.literals is None:
                ls = None
            else:
                ls.extend(r.literals)
            if not r.emptyseq: 
                acceptEmpty = False
                break # for r
        self.__mc4la = MatchCandidateForLookAhead(
                nodes=sorted(set(ns)) if ns is not None else None, 
                literals=sorted(set(ls)) if ls is not None else None, 
                emptyseq=acceptEmpty)
    
    def __match_tail(self, inpSeq, inpPos, r):
        if r is None: return None
        p, o = r
        len_inpSeq = len(inpSeq)
        curInpPos = inpPos + p
        outSeq = o if o.__class__ is list else list(o); o_xt = outSeq.extend
        for expr in self.__exprs[1:]:
            if curInpPos == len_inpSeq:
                r = expr._match_eon(inpSeq, curInpPos, None)
            else:
                lookAhead = inpSeq[curInpPos]
                if lookAhead.__class__ is list:
                    r = expr._match_node(inpSeq, curInpPos, lookAhead)
                else:
                    #assert lookAhead.__class__ is int #debug
                    r = expr._match_lit(inpSeq, curInpPos, ( lookAhead, inpSeq[curInpPos + 1] ))
            if r is None: return None
            p, o = r
            curInpPos += p; o_xt(o)
        return curInpPos - inpPos, outSeq
    
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        return self.__match_tail(inpSeq, inpPos, self.__expr0._match_node(inpSeq, inpPos, lookAheadNode))

    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        return self.__match_tail(inpSeq, inpPos, self.__expr0._match_lit(inpSeq, inpPos, lookAheadString))

    def _match_eon(self, inpSeq, inpPos, lookAheadDummy):
        outSeq = []
        for expr in self.__exprs:
            r = expr._match_eon(inpSeq, inpPos, lookAheadDummy)
            if r is None: return None
            p, o = r
            #assert p == 0
            outSeq.extend(o)
        return 0, outSeq

    def getMatchCandidateForLookAhead(self): 
        return self.__mc4la
            
    def optimized(self, objectpool={}):
        exprs = list(_seqflatener(self.__exprs))
        if not exprs: return Epsilon().optimized(objectpool)
        mergedExprs = [ exprs[0] ]
        for e in exprs[1:]:
            prev = mergedExprs[-1]
            m = prev.seq_merged(e) if hasattr(prev, "seq_merged") else None
            if m is not None:
                mergedExprs[-1] = m
            else:
                mergedExprs.append(e)
        return Epsilon().optimized(objectpool) if not mergedExprs else \
                 mergedExprs[0] if len(mergedExprs) == 1 else \
                 Seq(*mergedExprs)
        
class Repeat(TorqExpressionWithExpr):
    ''' Repeat expression matches a sequence, iff a N-time repetition of the internal expression matches the sequence.
        Here, N is a integer, lowerLimit <= N <= upperLimit.
        If lowerLimist is None, it will be regarded as 0.
        If upperLimit is None, it will be regarded as the infinite number.
    '''
    
    __slots__ = [ '__lowerLimit', '__upperLimit', '__mc4la' ]
    
    def __init__(self, expr, lowerLimit, upperLimit):
        assert lowerLimit >= 0
        assert upperLimit is None or upperLimit >= lowerLimit
        self.__lowerLimit, self.__upperLimit = lowerLimit, upperLimit
        self._set_expr(expr)
        mc4la = self.expr.getMatchCandidateForLookAhead()
        self.__mc4la = None if mc4la is None else \
                MatchCandidateForLookAhead(nodes=mc4la.nodes, literals=mc4la.literals, emptyseq=self.__lowerLimit == 0 or mc4la.emptyseq)
        
    def _match_node(self, inpSeq, inpPos, lookAhead):
        len_inpSeq = len(inpSeq)
        assert inpPos < len_inpSeq
        curInpPos = inpPos
        outSeq = []; o_xt = outSeq.extend
        
        ul = self.__upperLimit if self.__upperLimit is not None else (len_inpSeq - inpPos)
        # inpPos will increase 1 or more by a repetition so we can't repeat the following loop over (len_inpSeq - inpPos) times.
        
        count = 0 - self.__lowerLimit
        ul -= self.__lowerLimit
        while count < ul and curInpPos < len_inpSeq:
            lookAhead = inpSeq[curInpPos]
            if lookAhead.__class__ is list:
                r = self._expr._match_node(inpSeq, curInpPos, lookAhead)
            else:
                #assert lookAhead.__class__ is int #debug
                r = self._expr._match_lit(inpSeq, curInpPos, ( lookAhead, inpSeq[curInpPos + 1] ))
            if r is None:
                if count < 0: return None
                break # for count
            p, o = r
            if p == 0 and count >= 0: break # in order to avoid infinite loop
            curInpPos += p; o_xt(o)
            count += 1
        if curInpPos == len_inpSeq and count < 0:
            r = self._expr._match_eon(inpSeq, inpPos, None)
            if r is None: return None
            p, o = r
            #assert p == 0
            #assert not d
            if o.__class__ is not list: o = list(o)
            o_xt(o * -count)
        return curInpPos - inpPos, outSeq
    
    _match_lit = _match_node
    
    def _match_eon(self, inpSeq, inpPos, lookAheadDummy):
        r = self._expr._match_eon(inpSeq, inpPos, lookAheadDummy)
        if r is None:
            return _zeroLengthReturnValue if self.__lowerLimit == 0 else None
        p, o = r
        #assert p == 0
        if self.__lowerLimit != 0:
            if o.__class__ is not list: o = list(o)
            return 0, o * self.__lowerLimit
        return _zeroLengthReturnValue
    
    def _eq_i(self, right, alreadyComparedExprs):
        rightClassIsRpeatOrRepeatZeroOrOne = isinstance(right, Repeat) # this line could be "... = right.__class__ is Repeat or right.__class__ is RepeatZeroOrOne", if the language permits to write so.
        return rightClassIsRpeatOrRepeatZeroOrOne and \
                self.__lowerLimit == right.__lowerLimit and self.__upperLimit == right.__upperLimit and \
                self.expr._eq_i(right, alreadyComparedExprs)
        
    def __repr__(self): 
        return "Repeat(%s,%s,%s)" % ( repr(self.expr), repr(self.__lowerLimit), repr(self.__upperLimit) )
    
    def __hash__(self): return hash("Repeat") + hash(self.expr) + hash(self.__lowerLimit) + hash(self.__upperLimit)

    def getMatchCandidateForLookAhead(self): 
        return self.__mc4la
    
    @staticmethod
    def ZeroOrOne(expr): return _RepeatZeroOrOne(expr)

    @staticmethod
    def ZeroOrMore(expr): return Repeat(expr, 0, None)

    @staticmethod
    def OneOrMore(expr): return Repeat(expr, 1, None)
    
    def optimized(self, objectpool={}):
        LU = self.__lowerLimit, self.__upperLimit
        if LU == (0, 0) or self.expr.__class__ is Epsilon: return Epsilon().optimized(objectpool)
        if LU[0] != 0 and self.expr.__class__ is Never: return Never().optimized(objectpool)
        else:
            seo = self.expr.optimized(objectpool)
            if self.expr.__class__ is Search: return seo
            elif LU == (0, 1): return Repeat.ZeroOrOne(seo)
            elif LU == (0, None): return Repeat.ZeroOrMore(seo)
            elif LU == (1, 1): return seo
            elif LU == (1, None): return Repeat.OneOrMore(seo)
            else: return self
        
class _RepeatZeroOrOne(Repeat):
    __slots__ = [ ]
    
    def __init__(self, expr):
        Repeat.__init__(self, expr, 0, 1)
        
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        return self._expr._match_node(inpSeq, inpPos, lookAheadNode) or _zeroLengthReturnValue
    
    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        return self._expr._match_lit(inpSeq, inpPos, lookAheadString) or _zeroLengthReturnValue
   
    def _match_eon(self, inpSeq, inpPos, lookAheadDummy):
        return self._expr._match_eon(inpSeq, inpPos, lookAheadDummy) or _zeroLengthReturnValue

class Search(TorqExpressionWithExpr):
    ''' Search(expr) is almost identical to Repeat(Or(expr, Any()), 0, None).
        The difference is: when expr matches an empty sequence at some position of inpSeq,
        the former matches the entire input sequence. the latter matches the empty sequence.
    '''
    
    __slots__ = [ '__mc4la' ]
    
    def __init__(self, expr):
        self._set_expr(expr)
        mc4la = expr.getMatchCandidateForLookAhead()
        self.__mc4la = None if mc4la is None else MatchCandidateForLookAhead(nodes=mc4la.nodes, literals=mc4la.literals, emptyseq=True)
    
    def _match_node(self, inpSeq, inpPos, lookAhead):
        len_inpSeq = len(inpSeq)
        curInpPos = inpPos
        outSeq = []; o_xt = outSeq.extend; o_ap = outSeq.append
        while curInpPos < len_inpSeq:
            lookAhead = inpSeq[curInpPos]
            if lookAhead.__class__ is list:
                r = self._expr._match_node(inpSeq, curInpPos, lookAhead)
                if r is not None:
                    p, o = r
                    curInpPos += p; o_xt(o)
                if r is None or p == 0:
                    o_ap(lookAhead)
                    curInpPos += 1
            else:
                #assert lookAhead.__class__ is int #debug
                r = self._expr._match_lit(inpSeq, curInpPos, ( lookAhead, inpSeq[curInpPos + 1] ))
                if r is not None:
                    p, o = r
                    curInpPos += p; o_xt(o)
                if r is None or p == 0:
                    o_ap(lookAhead)
                    o_ap(inpSeq[curInpPos + 1])
                    curInpPos += 2
        if curInpPos == len_inpSeq:
            r = self._expr._match_eon(inpSeq, curInpPos, None)
            if r is not None:
                p, o = r
                #assert p == 0
                o_xt(o)
        return curInpPos - inpPos, outSeq
    
    _match_lit = _match_node
        
    def _match_eon(self, inpSeq, inpPos, lookAhead):
        return self._expr._match_eon(inpSeq, inpPos, lookAhead)
    
    def getMatchCandidateForLookAhead(self): 
        return self.__mc4la
    
    def optimized(self, objectpool={}):
        if self.expr.__class__ is Search:
            return self.expr.optimized(objectpool)
        return self
        
class InterpretError(StandardError):
    def __init__(self, message):
        StandardError.__init__(self, message)
        self.message = message
        self.stack = []

    def __repr__(self):
        return "InterpretError(%s,%s)" % ( repr(self.message), repr(self.stack) )

class InterpretErrorByErrorExpr(InterpretError):
    def __repr__(self):
        return "InterpretErrorByErrorExpr(%s,%s)" % ( repr(self.message), repr(self.stack) )
    
class ErrorExpr(TorqExpression):
    def __init__(self, message):
        self.message = message
    
    def _match_node(self, inpSeq, inpPos, lookAhead):
        e = InterpretErrorByErrorExpr(self.message)
        e.stack.insert(0, inpPos)
        raise e
        
    _match_lit = _match_eon = _match_node
    
    def __repr__(self): return "ErrorExpr(%s)" % repr(self.message)
    def __hash__(self): return hash("ErrorExpr") + hash(self.message)

    def _eq_i(self, right, alreadyComparedExprs):
        return right.__class__ is ErrorExpr and self.message == right.message
                
    def optimized(self, objectpool={}): return self

_emptyMc4la = MatchCandidateForLookAhead(emptyseq=True)

class Epsilon(TorqExpressionSingleton):
    ''' Epsilon expression matches any zero-length sequence.
    '''
    __slots__ = [ ]
    
    def _match_node(self, inpSeq, inpPos, lookAhead): return _zeroLengthReturnValue
    _match_lit = _match_eon = _match_node

    def getMatchCandidateForLookAhead(self): return _emptyMc4la

    def seq_merged(self, other): return other
    def or_merged(self, other): return self

_anyMc4la = MatchCandidateForLookAhead(nodes=None, literals=None, emptyseq=False)
    
class Any(TorqExpressionSingleton):
    ''' Any expression matches any length-1 sequence.
    '''
    
    __slots__ = [ ]

    def _match_node(self, inpSeq, inpPos, lookAhead): return 1, [ inpSeq[inpPos] ]
    def _match_lit(self, inpSeq, inpPos, lookAheadString): return 2, lookAheadString
    
    def getMatchCandidateForLookAhead(self): 
        return _anyMc4la
    
class Never(TorqExpressionSingleton):
    ''' Never expression does not match any sequence.
    '''
    
    __slots__ = [ ]
    
    def _match_node(self, inpSeq, inpPos, lookAhead): return None
    _match_lit = _match_eon = _match_node
    
    def seq_merged(self, other): return self
    def or_merged(self, other): return other
    
