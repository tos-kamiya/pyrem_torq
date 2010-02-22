import itertools

from pytorqy.utility import SingletonWoInitArgs

class InvalidRepetitionCount(ValueError):
    pass

_islist = list.__instancecheck__

_zeroLengthReturnValue = 0, (), ()

class TorqExpression(object):
    def expr_iter(self): 
        # will yield None, if the expression has an attribute 'expr' and its value is None
        # or if the expression has an attribute 'exprs', which contains None as an item
        raise StopIteration
        yield # dummy
    
    def __add__(self, other):
        return Seq.build(self, other)
    
    def __or__(self, other):
        return Or.build(self, other)
    
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
        return Repeat.build(self, lower, upper)
            
    def match(self, inpSeq, inpPos):
        assert inpPos >= 1
        len_inpSeq = len(inpSeq)
        assert _islist(inpSeq) and len_inpSeq >= 1
        if inpPos == len_inpSeq:
            r = self._match_eon(inpSeq, inpPos, None)
        else:
            lookAhead = inpSeq[inpPos]
            r = (self._match_node if _islist(lookAhead) else self._match_lit)(inpSeq, inpPos, lookAhead)
        if r is None: return 0, [], []
        p, o, d = r
        outSeq = []; outSeq.extend(o)
        dropSeq = d if _islist(d) else list(d)
        return p, outSeq, dropSeq
    
    def parse(self, inpSeq, dropSeq=None):
        posDelta, outSeq, _dropSeq = self.match(inpSeq, 1)
        if 1 + posDelta != len(inpSeq): return None
        if isinstance(dropSeq, list): dropSeq.append(_dropSeq)
        return [ inpSeq[0] ] + outSeq
    
    def _match_node(self, inpSeq, inpPos, lookAhead):
        pass
        # return None
    
    _match_lit = _match_eon = _match_node
    
    def required_node_literal_epsilon(self):
        # return a tuple: (list of node names, list of literals, zero-length match or not)
        # this method enumerates the items that can be accepted by the expression.
        # (the expression never accept items except for these items. )
        # if the expression can't assure such items, then just reruns None.
        return None
    
    def __eq__(self, right): 
        if not isinstance(right, self.__class__): return False
        subexprs = list(self.expr_iter())
        if subexprs: return subexprs == list(right.expr_iter())
    
    def __repr__(self): 
        subexprs = list(self.expr_iter())
        return "%s(%s)" % ( self.__class__.__name__, ",".join(map(repr, subexprs)) ) if subexprs else \
                "%s()" % self.__class__.__name__
        
    def __hash__(self):
        return hash(self.__class__.__name__) + sum(hash(e) for e in self.expr_iter())

class TorqExpressionWithExpr(TorqExpression):
    __slots__ = [ '_expr', '_expr_match_node', '_expr_match_lit', '_expr_match_eon' ]
    
    def getexpr(self): return self._expr
    expr = property(getexpr)
    
    def _set_expr(self, expr):
        assert isinstance(expr, TorqExpression)
        self._expr = expr
    
    def expr_iter(self):
        yield self._expr

def _orflatener(exprs):
    for e in exprs:
        if isinstance(e, Or):
            for i in _orflatener(e.exprs): yield i
        else: yield e

class Or(TorqExpression):
    __slots__ = [ '__exprs', '__ntbl_get', '__ltbl_get', '__elst', '__including_unknown_req', '__rnle' ]
    
    def __init__(self, *exprs):
        self._set_exprs(exprs)
    
    def getexprs(self): return self.__exprs
    exprs = property(getexprs)
    
    def _set_exprs(self, exprs):
        self.__exprs = exprs
        for expr in self.__exprs: assert isinstance(expr, TorqExpression)
        ntbl, ltbl, self.__elst, self.__including_unknown_req = Or._make_tables(self.__exprs)
        if self.__including_unknown_req:
            self.__rnle = None
        else:
            self.__rnle = sorted(ntbl.iterkeys()), sorted(ltbl.iterkeys()), not not self.__elst
        self.__ntbl_get = ntbl.get
        self.__ltbl_get = ltbl.get
    
    @staticmethod
    def _make_tables(exprs):
        exprAndReqs = [( expr, expr.required_node_literal_epsilon() ) for expr in exprs]
        ns, ls = [], []
        for _, r in exprAndReqs:
            if r is not None:
                ns.extend(r[0]); ls.extend(r[1])
        
        ntbl = dict(( lbl, [] ) for lbl in ns)
        ltbl = dict(( s, [] ) for s in ls)
        elst = []
        for expr, r in exprAndReqs:
            if r is not None:
                for lbl in r[0]: ntbl[lbl].append(expr)
                for s in r[1]: ltbl[s].append(expr)
                if r[2]: elst.append(expr)
            else:
                for L in itertools.chain(ntbl.itervalues(), ltbl.itervalues(), [ elst ]):
                    L.append(expr)
        return ntbl, ltbl, elst, None in list(r for _, r in exprAndReqs)
    
    def expr_iter(self):
        for e in self.__exprs: yield e
        
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        for expr in self.__ntbl_get(lookAheadNode[0], self.__elst):
            r = expr._match_node(inpSeq, inpPos, lookAheadNode)
            if r is not None:
                return r
        #else: return None
        
    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        for expr in self.__ltbl_get(lookAheadString, self.__elst):
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

    def required_node_literal_epsilon(self): return self.__rnle
            
    @staticmethod
    def build(*exprs):
        exprs = list(_orflatener(exprs))
        if not exprs: return Never()
        mergedExprs = [ exprs[0] ]
        for e in exprs[1:]:
            prev = mergedExprs[-1]
            m = prev.or_merged(e) if hasattr(prev, "or_merged") else None
            if m is not None:
                mergedExprs[-1] = m
            else:
                mergedExprs.append(e)
        if not mergedExprs: 
            return Never()
        if len(mergedExprs) == 1:
            return mergedExprs[0]
        return Or(*mergedExprs)

def _seqflatener(exprs):
    for e in exprs:
        if isinstance(e, Seq):
            for i in _seqflatener(e.exprs): yield i
        else: yield e

class Seq(TorqExpression):
    __slots__ = [ '__exprs', '__expr0' ]
    
    def getexprs(self): return self.__exprs
    exprs = property(getexprs)
    
    def _set_exprs(self, exprs):
        self.__exprs = tuple(exprs)
        for expr in self.__exprs: assert isinstance(expr, TorqExpression)
        self.__expr0 = self.__exprs[0] if self.__exprs else Epsilon()
    
    def expr_iter(self):
        for e in self.__exprs: yield e
        
    def __init__(self, *exprs):
        self._set_exprs(exprs)
    
    def __match_tail(self, inpSeq, inpPos, r):
        if r is None: return None
        p, o, d = r
        len_inpSeq = len(inpSeq)
        curInpPos = inpPos + p
        outSeq = o if _islist(o) else list(o)
        dropSeq = d if _islist(d) else list(d)
        for expr in self.__exprs[1:]:
            if curInpPos == len_inpSeq:
                r = expr._match_eon(inpSeq, curInpPos, None)
            else:
                lookAhead = inpSeq[curInpPos]
                r = (expr._match_node if _islist(lookAhead) else expr._match_lit)(inpSeq, curInpPos, lookAhead)
            if r is None: return None
            p, o, d = r
            curInpPos += p
            outSeq.extend(o)
            dropSeq.extend(d)
        return curInpPos - inpPos, outSeq, dropSeq
    
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        return self.__match_tail(inpSeq, inpPos, self.__expr0._match_node(inpSeq, inpPos, lookAheadNode))

    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        return self.__match_tail(inpSeq, inpPos, self.__expr0._match_lit(inpSeq, inpPos, lookAheadString))

    def _match_eon(self, inpSeq, inpPos, lookAheadDummy):
        outSeq = []
        for expr in self.__exprs:
            r = expr._match_eon(inpSeq, inpPos, lookAheadDummy)
            if r is None: return None
            p, o, d = r
            assert p == 0
            assert not d
            outSeq.extend(o)
        return 0, outSeq, ()

    def required_node_literal_epsilon(self):
        if not self.__exprs:
            return (), (), True
        ns, ls, epsilon = [], [], True
        for r in (expr.required_node_literal_epsilon() for expr in self.exprs):
            if r is None: return None
            ns.extend(r[0]); ls.extend(r[1])
            if not r[2]: 
                epsilon = False
                break # for r
        return sorted(set(ns)), sorted(set(ls)), epsilon
            
    @staticmethod
    def build(*exprs):
        exprs = list(_seqflatener(exprs))
        if not exprs: return Epsilon()
        mergedExprs = [ exprs[0] ]
        for e in exprs[1:]:
            prev = mergedExprs[-1]
            m = prev.seq_merged(e) if hasattr(prev, "seq_merged") else None
            if m is not None:
                mergedExprs[-1] = m
            else:
                mergedExprs.append(e)
        if not mergedExprs:
            return Epsilon()
        if len(mergedExprs) == 1:
            return mergedExprs[0]
        return Seq(*mergedExprs)

class Repeat(TorqExpressionWithExpr):
    __slots__ = [ '__lowerLimit', '__upperLimit' ]
    
    def __init__(self, expr, lowerLimit, upperLimit):
        assert lowerLimit >= 0
        assert upperLimit is None or upperLimit >= lowerLimit
        self.__lowerLimit, self.__upperLimit = lowerLimit, upperLimit
        self._set_expr(expr)
        
    def _match_node(self, inpSeq, inpPos, lookAhead):
        len_inpSeq = len(inpSeq)
        curInpPos = inpPos
        outSeq = []
        dropSeq = []
        for count in (xrange(-self.__lowerLimit, self.__upperLimit - self.__lowerLimit) if self.__upperLimit is not None else \
                itertools.count(-self.__lowerLimit)):
            if curInpPos == len_inpSeq:
                r = self._expr._match_eon(inpSeq, curInpPos, None)
            else:
                lookAhead = inpSeq[curInpPos]
                r = (self._expr._match_node if _islist(lookAhead) else self._expr._match_lit)(inpSeq, curInpPos, lookAhead)
            if r is None:
                if count < 0: return None
                break # for count
            p, o, d = r
            if p == 0 and count >= 0: break # in order to avoid infinite loop
            curInpPos += p
            outSeq.extend(o)
            dropSeq.extend(d)
        return curInpPos - inpPos, outSeq, dropSeq
    
    _match_lit = _match_node
    
    def _match_eon(self, inpSeq, inpPos, lookAheadDummy):
        r = self._expr._match_eon(inpSeq, inpPos, lookAheadDummy)
        if r is None:
            return _zeroLengthReturnValue if self.__lowerLimit == 0 else None
        p, o, d = r
        assert p == 0
        assert not d
        if self.__lowerLimit != 0:
            return 0, o * self.__lowerLimit, ()
        return _zeroLengthReturnValue
    
    def __eq__(self, right): 
        return isinstance(right, Repeat) and self.expr == right.expr and \
                self.__lowerLimit == right.__lowerLimit and self.__upperLimit == right.__upperLimit
    
    def __repr__(self): 
        return "Repeat(%s,%s,%s)" % ( repr(self.expr), repr(self.__lowerLimit), repr(self.__upperLimit) )
    
    def __hash__(self): return hash("Repeat") + hash(self.expr) + hash(self.__lowerLimit) + hash(self.__upperLimit)

    def required_node_literal_epsilon(self):
        r = self.expr.required_node_literal_epsilon()
        if self.__lowerLimit >= 1:
            return r
        else:
            if r is None: 
                return None
            else: 
                return r[0], r[1], True
    
    @staticmethod
    def ZeroOrOne(expr): return _RepeatZeroOrOne(expr)

    @staticmethod
    def ZeroOrMore(expr): return Repeat(expr, 0, None)

    @staticmethod
    def OneOrMore(expr): return Repeat(expr, 1, None)
    
    @staticmethod
    def build(expr, lowerLimit, upperLimit):
        LU = lowerLimit, upperLimit
        if LU == (0, 1): return _RepeatZeroOrOne(expr)
        elif LU == (0, None): return Repeat.ZeroOrMore(expr)
        elif LU == (1, None): return Repeat.OneOrMore(expr)
        else: return Repeat(expr, lowerLimit, upperLimit)

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

class Scan(TorqExpressionWithExpr):
    # Scan(expr) is almost identical to Repeat(Or(expr, Any()), 0, None).
    # The difference is: when expr matches an empty sequence at some position of inpSeq,
    # the former matches the entire input sequence. the latter matches the empty sequence.
    
    __slots__ = [ ]
    
    def __init__(self, expr):
        self._set_expr(expr)
        
    def _match_node(self, inpSeq, inpPos, lookAhead):
        len_inpSeq = len(inpSeq)
        curInpPos = inpPos
        outSeq = []; o_xt = outSeq.extend; o_ap = outSeq.append
        dropSeq = []; d_xt = dropSeq.extend
        while curInpPos < len_inpSeq:
            lookAhead = inpSeq[curInpPos]
            r = (self._expr._match_node if _islist(lookAhead) else self._expr._match_lit)(inpSeq, curInpPos, lookAhead)
            if r is None:
                curInpPos += 1
                o_ap(lookAhead)
            else:
                p, o, d = r
                curInpPos += p
                o_xt(o)
                d_xt(d)
                if p == 0:
                    curInpPos += 1
                    o_ap(lookAhead)
        if curInpPos == len_inpSeq:
            r = self._expr._match_eon(inpSeq, curInpPos, None)
            if r is not None:
                p, o, d = r
                assert p == 0
                o_xt(o)
                d_xt(d)
        return curInpPos - inpPos, outSeq, dropSeq
    
    _match_lit = _match_node
    
    def _match_eon(self, inpSeq, inpPos, lookAhead):
        return self._expr._match_eon(inpSeq, inpPos, lookAhead)
    
    def required_node_literal_epsilon(self):
        r = self.expr.required_node_literal_epsilon()
        if r is None: 
            return None
        else: 
            return r[0], r[1], True
    
    @staticmethod
    def build(expr): return Scan(expr)

class InterpretError(StandardError):
    def __init__(self, message):
        StandardError.__init__(self, message)
        self.stack = []

class ErrorExpr(TorqExpression):
    def __init__(self, message):
        self.message = message
    
    def _match_node(self, inpSeq, inpPos, lookAhead):
        e = InterpretError(self.message)
        e.stack.insert(0, inpPos)
        raise e
        
    _match_lit = _match_eon = _match_node
    
    @staticmethod
    def build(message): return ErrorExpr(message)

class Epsilon(TorqExpression): # singleton
    __metaclass__ = SingletonWoInitArgs
    __slots__ = [ ]
    
    def _match_node(self, inpSeq, inpPos, lookAhead): return _zeroLengthReturnValue
    _match_lit = _match_eon = _match_node

    def required_node_literal_epsilon(self): return (), (), True
    
    def seq_merged(self, other): return other
    def or_merged(self, other): return self
    
    @staticmethod
    def build(): return Epsilon()
    
class Any(TorqExpression): # singleton
    __metaclass__ = SingletonWoInitArgs
    __slots__ = [ ]

    def _match_node(self, inpSeq, inpPos, lookAhead): 
        return 1, [ inpSeq[inpPos] ], ()
    _match_lit = _match_node
    
    @staticmethod
    def build(): return Any()

class Never(TorqExpression): # singleton
    __metaclass__ = SingletonWoInitArgs
    __slots__ = [ ]
    
    def seq_merged(self, other): return self
    def or_merged(self, other): return other
    
    @staticmethod
    def build(): return Never()
