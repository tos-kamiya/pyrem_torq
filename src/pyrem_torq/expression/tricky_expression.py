from pyrem_torq.utility import SingletonWoInitArgs as _SingletonWoInitArgs

from base_expression import *
from literal_expression import Literal, LiteralClass
from node_expression import Node, NodeClass

_zeroLengthReturnValue = 0, (), ()

class Req(TorqExpressionWithExpr):
    __slots__ = [ ]
    
    def __init__(self, expr):
        self._set_expr(expr)
    
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        if self._expr._match_node(inpSeq, inpPos, lookAheadNode) is not None: return _zeroLengthReturnValue

    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        if self._expr._match_lit(inpSeq, inpPos, lookAheadString) is not None: return _zeroLengthReturnValue

    def _match_eon(self, inpSeq, inpPos, lookAheadDummy):
        if self._expr._match_eon(inpSeq, inpPos, lookAheadDummy) is not None: return _zeroLengthReturnValue
    
    def required_node_literal_epsilon(self):
        return self.expr.required_node_literal_epsilon()
            
    def seq_merged(self, other):
        if isinstance(self.expr, ( Literal, LiteralClass, Node, NodeClass )):
            rs = self.required_node_literal_epsilon()
            ro = other.required_node_literal_epsilon()
            if rs is None or ro is None: return None
            
            selfAcceptsEmpty = not not rs[2]
            otherAcceptsEmpty = not not ro[2]
            if selfAcceptsEmpty >= otherAcceptsEmpty and \
                    set(rs[0]).issuperset(set(ro[0])) and \
                    set(rs[1]).issuperset(set(ro[1])):
                # in this case, self's requirement is equivalent or superset to other's requirement.
                # so self will not do filter out other than other does.
                return other
        
    @staticmethod
    def build(expr): 
        if isinstance(expr, ( Never, Epsilon )):
            return expr
        return Req(expr)

class Xcp(TorqExpressionWithExpr):
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
        if isinstance(right, Any):
            return XcpThenAny.build(self.expr) 

    @staticmethod
    def build(expr): 
        if isinstance(expr, Epsilon):
            return Never()
        elif isinstance(expr, Never):
            return Epsilon()
        return Xcp(expr)

class EndOfNode(TorqExpression): # singleton
    __metaclass__ = _SingletonWoInitArgs
    __slots__ = [ ]
    
    def _match_eon(self, inpSeq, curInpPos, lookAheadDummy): return _zeroLengthReturnValue

    def required_node_literal_epsilon(self):
        return (), (), True
            
    @staticmethod
    def build(): return EndOfNode()

class BeginOfNode(TorqExpression): # singleton
    __metaclass__ = _SingletonWoInitArgs
    __slots__ = [ ]
    
    def _match_node(self, inpSeq, inpPos, lookAhead):
        if inpPos == 1: return _zeroLengthReturnValue
        #return None
        
    _match_lit = _match_node

    def required_node_literal_epsilon(self):
        return (), (), True
            
    @staticmethod
    def build(): return BeginOfNode()

class XcpThenAny(TorqExpressionWithExpr):
    __slots__ = [ ]
    
    def __init__(self, expr):
        self._set_expr(expr)
    
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        if self._expr._match_node(inpSeq, inpPos, lookAheadNode) is None: 
            return 1, ( lookAheadNode, ), ()
    
    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        if self._expr._match_lit(inpSeq, inpPos, lookAheadString) is None: 
            return 1, ( lookAheadString, ), ()
        
    @staticmethod
    def build(expr): 
        if isinstance(expr, ( Epsilon, Any )):
            return Never()
        elif isinstance(expr, Never):
            return Any()
        return XcpThenAny(expr)
    
