from base_expression import *
from literal_expression import Literal, LiteralClass
from node_expression import Node, NodeClass

_zeroLengthReturnValue = 0, ()

class Require(TorqExpressionWithExpr):
    ''' Require expression matches to a sequence which the internal expression matches.
       When matches, do nothing to the input sequence, the output sequence.
    '''
    
    __slots__ = [ ]
    
    def __init__(self, expr):
        self._set_expr(expr)
    
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        if self._expr._match_node(inpSeq, inpPos, lookAheadNode) is not None: return _zeroLengthReturnValue

    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        if self._expr._match_lit(inpSeq, inpPos, lookAheadString) is not None: return _zeroLengthReturnValue

    def _match_eon(self, inpSeq, inpPos, lookAheadDummy):
        if self._expr._match_eon(inpSeq, inpPos, lookAheadDummy) is not None: return _zeroLengthReturnValue
    
    def getMatchCandidateForLookAhead(self): 
        return self.expr.getMatchCandidateForLookAhead()
            
    def seq_merged(self, other):
        if self.expr.__class__ is Literal or self.expr.__class__ is LiteralClass or self.expr.__class__ is Node or self.expr.__class__ is NodeClass:
            rs = self.getMatchCandidateForLookAhead()
            ro = other.getMatchCandidateForLookAhead()
            if rs is None or ro is None: return None
            
            selfAcceptsEmpty = not not rs[2]
            otherAcceptsEmpty = not not ro[2]
            if selfAcceptsEmpty >= otherAcceptsEmpty and \
                    set(rs[0]).issuperset(set(ro[0])) and \
                    set(rs[1]).issuperset(set(ro[1])):
                # in this case, self's requirement is equivalent or superset to other's requirement.
                # so self will not do filter out other than other does.
                return other
        
    def optimized(self, objectpool={}):
        if self.expr.__class__ is Never or self.expr.__class__ is Epsilon:
            return self.expr.optimized(objectpool)
        return self

class RequireBut(TorqExpressionWithExpr):
    ''' Require expression matches to a sequence which the internal expression DOES NOT matches.
       When matches, do nothing to the input sequence, the output sequence, the dropped sequence.
    '''
    
    __slots__ = [ ]
    
    def __init__(self, expr):
        self._set_expr(expr)
    
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        if self._expr._match_node(inpSeq, inpPos, lookAheadNode) is None: return _zeroLengthReturnValue

    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        if self._expr._match_lit(inpSeq, inpPos, lookAheadString) is None: return _zeroLengthReturnValue
    
    def _match_eon(self, inpSeq, inpPos, lookAheadDummy):
        if self._expr._match_eon(inpSeq, inpPos, lookAheadDummy) is None: return _zeroLengthReturnValue
    
    def seq_merged(self, right):
        if right.__class__ is Any:
            return AnyBut(self.expr) 

    def getMatchCandidateForLookAhead(self): 
        return MatchCandidateForLookAhead(nodes=None, literals=None, 
                emptyseq=not self.expr.getMatchCandidateForLookAhead().emptyseq)
    
    def optimized(self, objectpool={}):
        if self.expr.__class__ is Never:
            return Epsilon().optimized(objectpool)
        elif self.expr.__class__ is Epsilon:
            return Never().optimized(objectpool)
        return self
    
_emptyMc4la = MatchCandidateForLookAhead(emptyseq=True)

class EndOfNode(TorqExpressionSingleton):
    ''' EndOfNode expression matches to a position of end-of-sequence.
       When matches, do nothing to the input sequence, the output sequence, the dropped sequence.
    '''
    
    __slots__ = [ ]
    
    def _match_eon(self, inpSeq, curInpPos, lookAheadDummy): return _zeroLengthReturnValue

    def getMatchCandidateForLookAhead(self): return _emptyMc4la

_insertingMc4la = MatchCandidateForLookAhead(nodes=None, literals=None, emptyseq=True)
            
class BeginOfNode(TorqExpressionSingleton):
    ''' BeginOfNode expression matches to a position of beginning-of-sequence.
       When matches, do nothing to the input sequence, the output sequence, the dropped sequence.
    '''
    
    __slots__ = [ ]
    
    def _match_node(self, inpSeq, inpPos, lookAhead):
        if inpPos == 1: return _zeroLengthReturnValue
        #return None
        
    _match_lit = _match_node

    def getMatchCandidateForLookAhead(self): 
        return _insertingMc4la

_atLeastOneItemMc4la = MatchCandidateForLookAhead(nodes=None, literals=None)            

class AnyBut(TorqExpressionWithExpr):
    ''' AnyBut(expr) is equal to Seq(RequireBut(expr), Any()).
    '''
    
    __slots__ = [ ]
    
    def __init__(self, expr):
        self._set_expr(expr)
    
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        if self._expr._match_node(inpSeq, inpPos, lookAheadNode) is None: 
            return 1, ( lookAheadNode, )
    
    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        #assert len(lookAheadString) == 2
        if self._expr._match_lit(inpSeq, inpPos, lookAheadString) is None: 
            return 2, lookAheadString
        
    def getMatchCandidateForLookAhead(self): return _atLeastOneItemMc4la
    
    def optimized(self, objectpool={}):
        if self.expr.__class__ is Never:
            return Any().optimized(objectpool)
        elif self.expr.__class__ is Epsilon or self.expr.__class__ is Any:
            return Never().optimized(objectpool)
        return self
    
