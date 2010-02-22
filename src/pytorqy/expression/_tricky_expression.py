from ._expression import *

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
    __metaclass__ = SingletonWoInitArgs
    __slots__ = [ ]
    
    def _match_eon(self, inpSeq, curInpPos, lookAheadDummy): return _zeroLengthReturnValue

    def required_node_literal_epsilon(self):
        return (), (), True
            
    @staticmethod
    def build(): return EndOfNode()

class BeginOfNode(TorqExpression): # singleton
    __metaclass__ = SingletonWoInitArgs
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
            return 1, [ lookAheadNode ], ()
    
    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        if self._expr._match_lit(inpSeq, inpPos, lookAheadString) is None: 
            return 1, [ lookAheadString ], ()
        
    @staticmethod
    def build(expr): 
        if isinstance(expr, ( Epsilon, Any )):
            return Never()
        elif isinstance(expr, Never):
            return Any()
        return XcpThenAny(expr)
