#coding: utf-8

from base_expression import *

_zeroLengthReturnValue = 0, ()
_emptyMc4la = MatchCandidateForLookAhead(emptyseq=True)


class Require(TorqExpressionWithExpr):
    ''' Require expression matches to a sequence which the internal expression matches.
        When matches, do nothing to the input sequence, the output sequence.
    '''

    __slots__ = []

    def __init__(self, expr):
        self._set_expr(expr)
    
    def _calc_mc4la(self): pass
    
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        if self._expr._match_node(inpSeq, inpPos, lookAheadNode) is not None: return _zeroLengthReturnValue

    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        if self._expr._match_lit(inpSeq, inpPos, lookAheadString) is not None: return _zeroLengthReturnValue

    def _match_eon(self, inpSeq, inpPos, lookAheadDummy):
        if self._expr._match_eon(inpSeq, inpPos, lookAheadDummy) is not None: return _zeroLengthReturnValue
    
    def getMatchCandidateForLookAhead(self): return self._expr.getMatchCandidateForLookAhead()
    def updateMatchCandidateForLookAhead(self): self._expr.updateMatchCandidateForLookAhead()

    def _isLeftRecursive_i(self, target, visitedExprIdSet):
        if self is target:
            return True
        id_self = id(self)
        if id_self in visitedExprIdSet:
            return False
        visitedExprIdSet.add(id_self)
        return self.expr._isLeftRecursive_i(target, visitedExprIdSet)
            
class RequireBut(TorqExpressionWithExpr):
    ''' Require expression matches to a sequence which the internal expression DOES NOT matches.
       When matches, do nothing to the input sequence, the output sequence, the dropped sequence.
    '''
    
    __slots__ = []
    
    def __init__(self, expr):
        self._set_expr(expr)
    
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        if self._expr._match_node(inpSeq, inpPos, lookAheadNode) is None: return _zeroLengthReturnValue

    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        if self._expr._match_lit(inpSeq, inpPos, lookAheadString) is None: return _zeroLengthReturnValue
    
    def _match_eon(self, inpSeq, inpPos, lookAheadDummy):
        if self._expr._match_eon(inpSeq, inpPos, lookAheadDummy) is None: return _zeroLengthReturnValue

    def getMatchCandidateForLookAhead(self): return _emptyMc4la
    def updateMatchCandidateForLookAhead(self): pass
    
    def _calc_mc4la(self): pass
    
    def _isLeftRecursive_i(self, target, visitedExprIdSet):
        if self is target:
            return True
        id_self = id(self)
        if id_self in visitedExprIdSet:
            return False
        visitedExprIdSet.add(id_self)
        return self.expr._isLeftRecursive_i(target, visitedExprIdSet)
            
class EndOfNode(TorqExpressionSingleton):
    ''' EndOfNode expression matches to a position of end-of-sequence.
       When matches, do nothing to the input sequence, the output sequence, the dropped sequence.
    '''

    __slots__ = []

    def _match_eon(self, inpSeq, curInpPos, lookAheadDummy): return _zeroLengthReturnValue

    def getMatchCandidateForLookAhead(self): return _emptyMc4la

_insertingMc4la = MatchCandidateForLookAhead(nodes=ANY_ITEM, literals=ANY_ITEM, emptyseq=True)
            
class BeginOfNode(TorqExpressionSingleton):
    ''' BeginOfNode expression matches to a position of beginning-of-sequence.
       When matches, do nothing to the input sequence, the output sequence, the dropped sequence.
    '''

    __slots__ = []

    def _match_node(self, inpSeq, inpPos, lookAhead):
        if inpPos == 1: return _zeroLengthReturnValue
        #return None
        
    _match_lit = _match_node

    def getMatchCandidateForLookAhead(self): 
        return _insertingMc4la

_atLeastOneItemMc4la = MatchCandidateForLookAhead(nodes=ANY_ITEM, literals=ANY_ITEM)


class AnyBut(TorqExpressionWithExpr):
    ''' AnyBut(expr) is equal to Seq(RequireBut(expr), Any()). '''

    __slots__ = []

    def __init__(self, expr):
        self._set_expr(expr)
    
    def _calc_mc4la(self): pass
    
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        if self._expr._match_node(inpSeq, inpPos, lookAheadNode) is None:
            return 1, (lookAheadNode, )

    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        #assert len(lookAheadString) == 2
        if self._expr._match_lit(inpSeq, inpPos, lookAheadString) is None: 
            return 2, lookAheadString
        
    def getMatchCandidateForLookAhead(self): return _atLeastOneItemMc4la
    
    def _isLeftRecursive_i(self, target, visitedExprIdSet):
        id_self = id(self)
        if id_self in visitedExprIdSet:
            return False
        visitedExprIdSet.add(id_self)
        return self.expr is target or self.expr._isLeftRecursive_i(target, visitedExprIdSet)


class Join(TorqExpression):
    ''' Join(sepExpr, itemExpr, lowerLimit, upperLimit) is equal to
        Seq(itemExpr, Repeat(sepExpr, itemExpr, lowerLimit - 1, upperLimit - 1))
        when lowerLimit >= 1.
        Repeat(Seq(itemExpr, Repeat(sepExpr, itemExpr, 0, upperLimit - 1)), 0, 1)
        when lowerLimit == 0.
    '''

    __slots__ = ['__lowerLimit', '__upperLimit', '__mc4la', '_itemExpr', '__sepExpr', '__tailExpr']

    def __init__(self, sepExpr, itemExpr, lowerLimit, upperLimit):
        assert lowerLimit >= 0
        assert upperLimit is None or upperLimit >= lowerLimit
        self.__lowerLimit, self.__upperLimit = lowerLimit, upperLimit
        self._itemExpr = itemExpr
        self.__sepExpr = sepExpr
        self._calc_mc4la()

    def extract_exprs(self):
        return [self._itemExpr, self.__sepExpr]

    def _calc_mc4la(self):
        self.__tailExpr = Seq(self.__sepExpr, self._itemExpr)
        mc4laItem = self._itemExpr.getMatchCandidateForLookAhead()
        if mc4laItem is None:
            self.__mc4la = None
        else:
            if not mc4laItem.emptyseq:
                self.__mc4la = mc4laItem.modified(emptyseq=self.__lowerLimit == 0)
            else:
                mc4laSep = self.__sepExpr.getMatchCandidateForLookAhead()
                if mc4laSep is None:
                    self.__mc4la = None
                else:
                    m = MatchCandidateForLookAhead(nodes=mc4laItem.nodes | mc4laSep.nodes,
                        literals=mc4laItem.literals | mc4laSep.literals,
                        emptyseq=mc4laItem.emptyseq or mc4laSep.emptyseq)
                    self.__mc4la = m.modified(emptyseq=self.__lowerLimit == 0)
    
    def updateMatchCandidateForLookAhead(self):
        self._itemExpr.updateMatchCandidateForLookAhead()
        mc4laItem = self._itemExpr.getMatchCandidateForLookAhead()
        if mc4laItem is not None and mc4laItem.emptyseq:
            self.__sepExpr.updateMatchCandidateForLookAhead()
        self._calc_mc4la()
        
    def _match_node(self, inpSeq, inpPos, lookAhead):
        len_inpSeq = len(inpSeq)
        assert inpPos < len_inpSeq
        curInpPos = inpPos
        outSeq = []; o_xt = outSeq.extend
        
        ul = self.__upperLimit if self.__upperLimit is not None else (len_inpSeq - inpPos)
        # inpPos will increase 1 or more by a repetition so we can't repeat the following loop over (len_inpSeq - inpPos) times.

        expr = self._itemExpr
        count = 0 - self.__lowerLimit
        ul -= self.__lowerLimit
        while count < ul and curInpPos < len_inpSeq:
            lookAhead = inpSeq[curInpPos]
            if lookAhead.__class__ is list:
                r = expr._match_node(inpSeq, curInpPos, lookAhead)
            else:
                #assert lookAhead.__class__ is int #debug
                r = expr._match_lit(inpSeq, curInpPos, (lookAhead, inpSeq[curInpPos + 1]))
            if r is None:
                if count < 0: return None
                break  # for count
            p, o = r
            if p == 0 and count >= 0: break  # in order to avoid infinite loop
            curInpPos += p; o_xt(o)
            count += 1
            expr = self.__tailExpr
        if curInpPos == len_inpSeq and count < 0:
            r = self.__tailExpr._match_eon(inpSeq, inpPos, None)
            if r is None: return None
            p, o = r
            #assert p == 0
            if o.__class__ is not list: o = list(o)
            o_xt(o * -count)
        return curInpPos - inpPos, outSeq
    
    _match_lit = _match_node
    
    def _match_eon(self, inpSeq, inpPos, lookAheadDummy):
        rItem = self._itemExpr._match_eon(inpSeq, inpPos, lookAheadDummy)
        if rItem is None:
            return _zeroLengthReturnValue if self.__lowerLimit == 0 else None
        rTail = self.__tailExpr._match_eon(inpSeq, inpPos, lookAheadDummy)
        if rTail is None:
            return _zeroLengthReturnValue if self.__lowerLimit == 0 else None
        #assert rItem[0] == 0
        #assert rTail[0] == 0
        if self.__lowerLimit != 0:
            oItem = rItem[1]
            oTail = rTail[1]
            if oItem.__class__ is not list: oItem = list(oItem)
            if oTail.__class__ is not list: oTail = list(oTail)
            return 0, oItem + oTail * (self.__lowerLimit - 1)
        return _zeroLengthReturnValue
    
    def _eq_i(self, right, alreadyComparedExprs):
        return right.__class__ is Join and \
                self.__lowerLimit == right.__lowerLimit and self.__upperLimit == right.__upperLimit and \
                self._itemExpr._eq_i(right._itemExpr, alreadyComparedExprs) and \
                self.__seqExpr._eq_i(right.__seqExpr, alreadyComparedExprs)

    def __repr__(self):
        return "Join(%s,%s,%s,%s)" % (repr(self.__sepExpr), (self._itemExpr), repr(self.__lowerLimit), repr(self.__upperLimit))

    def __hash__(self): return hash("Join") + hash(self.__sepExpr) + hash(self._itemExpr) + hash(self.__lowerLimit) + hash(self.__upperLimit)

    def getMatchCandidateForLookAhead(self): 
        return self.__mc4la
    
    @staticmethod
    def ZeroOrOne(sepExpr, itemExpr): return Repeat.ZeroOrOne(itemExpr)

    @staticmethod
    def ZeroOrMore(sepExpr, itemExpr): return Join(sepExpr, itemExpr, 0, None)

    @staticmethod
    def OneOrMore(sepExpr, itemExpr): return Join(sepExpr, itemExpr, 1, None)
        
    def _isLeftRecursive_i(self, target, visitedExprIdSet):
        id_self = id(self)
        if id_self in visitedExprIdSet:
            return False
        visitedExprIdSet.add(id_self)
        if self._itemExpr.getMatchCandidateForLookAhead().emptyseq:
            return self._itemExpr is target or self.__sepExpr is target or \
                    self._itemExpr._isLeftRecursive_i(target, visitedExprIdSet) or self.__seqExpr._isLeftRecursive_i(target, visitedExprIdSet)
        else:
            return self._itemExpr is target or self.__expr._isLeftRecursive_i(target, visitedExprIdSet)


class BuildToNodeIfYet(TorqExpressionWithExpr):
    ''' BuildToNodeIfYet expression is similar to BuildToNode expression, except for
        BuildToNodeIfYet will enclose the sequence when the sequence is already 
        the named node. 
        E.g. BuildToNodeIfYet(label, BuildToNode(label, expr)) is equivalent to BuildToNode(label, expr).
    '''

    __slots__ = ['__newLabel']

    def __init__(self, newLabel, expr):
        #assert expr is not None # use Node, instead!
        self._set_expr(expr)
        assert newLabel
        self.__newLabel = newLabel
    
    def getnewlabel(self): return self.__newLabel
    newLabel = property(getnewlabel)
    
    def _calc_mc4la(self): pass

    def extract_new_labels(self): return [self.__newLabel]

    def __enclose_if_not(self, r):
        p, o = r
        if o.__class__ is not list:
            o = list(o)
        if len(o) == 1 and o[0].__class__ is list and len(o[0]) == 2 and o[0][0] == self.__newLabel:
            return r
        else:
            newNode = [self.__newLabel]; newNode.extend(o)
            return p, [newNode]

    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        r = self._expr._match_node(inpSeq, inpPos, lookAheadNode)
        if r:
            return self.__enclose_if_not(r)
    
    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        r = self._expr._match_lit(inpSeq, inpPos, lookAheadString)
        if r:
            return self.__enclose_if_not(r)
    
    def _match_eon(self, inpSeq, inpPos, lookAheadDummy):
        r = self._expr._match_eon(inpSeq, inpPos, lookAheadDummy)
        if r:
            return self.__enclose_if_not(r)
    
    def _eq_i(self, right, alreadyComparedExprs):
        return right.__class__ is BuildToNodeIfYet and self.__newLabel == right.__newLabel and \
                self.expr._eq_i(right.expr, alreadyComparedExprs)

    def __repr__(self): return "BuildToNodeIfYet(%s,%s)" % (repr(self.__newLabel), repr(self.expr))

    def __hash__(self): return hash("BuildToNodeIfYet") + hash(self.__newLabel) + hash(self.expr)

    def getMatchCandidateForLookAhead(self): return self._expr.getMatchCandidateForLookAhead()
    def updateMatchCandidateForLookAhead(self): self._expr.updateMatchCandidateForLookAhead()

    def _isLeftRecursive_i(self, target, visitedExprIdSet):
        id_self = id(self)
        if id_self in visitedExprIdSet:
            return False
        visitedExprIdSet.add(id_self)
        return self.expr is target or self.expr._isLeftRecursive_i(target, visitedExprIdSet)

