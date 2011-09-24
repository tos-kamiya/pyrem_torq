from base_expression import TorqExpression, InterpretError, LeftRecursionUndecided

class _UninterpretableNode(TorqExpression):
    __slots__ = [ '__expr' ]
    
    def __init__(self, expr):
        self.__expr = expr
    
    def _match_node(self, inpSeq, inpPos, lookAheadNode): self.expr.__raise_error(inpPos)
    _match_lit = _match_eon = _match_node

class Holder(TorqExpression):
    ''' A special expression, which is used as a place holder of an expression.
        A marker object has two properties: name and expr.
        The name property is a label of the marker object.
        The expr property is an internal expression of the marker object.
        When evaluated an expression, a marker object behaves as if it were the internal expression.
    '''

    __slots__ = [ '__name', '__expr', '__mc4la' ]
    
    def __init__(self, name=None):
        self.__name = name
        self.__expr = _UninterpretableNode(self)
    
    def __repr__(self): return "Holder(name=%s)" % repr(self.__name)
    def __hash__(self): return hash("Holder") + hash(self.__name)

    def _eq_i(self, right, alreadyComparedExprs):
        return right.__class__ is Holder and \
                self.__name == right.__name and \
                self.__expr._eq_i(right.__expr, alreadyComparedExprs)
        
    def getname(self): return self.__name
    def setname(self, name): self.__name = name
    name = property(getname, setname, None)
    
    def getexpr(self): 
        if isinstance(self.__expr, _UninterpretableNode): return None
        return self.__expr
    
    def setexpr(self, expr):
        if expr is None:
            self.__expr = _UninterpretableNode(self)
        elif isinstance(expr, TorqExpression):
            self.__expr = expr
        else:
            raise TypeError("Holder.setexpr()'s argument must be an TorqExpression")
        self.updateMatchCandidateForLookAhead()
    expr = property(getexpr, setexpr, None)
    
    def extract_exprs(self): return [ self.__expr ]

    def updateMatchCandidateForLookAhead(self):
        if not isinstance(self.__expr, _UninterpretableNode):
            self.__mc4la = self.__expr.getMatchCandidateForLookAhead()
            # don't execute: self.__expr.updateMatchCandidateForLookAhead()
            # such a call will cause infinte recursion!
        else:
            self.__mc4la = None
        
    def getMatchCandidateForLookAhead(self): return self.__mc4la 
    
    def __raise_error(self, inpPos):
        e = InterpretError("Interpreting Holder w/o valid expression: '%s'" % self.__name)
        e.stack.insert(0, inpPos)
        raise e
    
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        return self.__expr._match_node(inpSeq, inpPos, lookAheadNode)
    
    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        return self.__expr._match_lit(inpSeq, inpPos, lookAheadString)

    def _match_eon(self, inpSeq, inpPos, lookAheadDummy):
        return self.__expr._match_eon(inpSeq, inpPos, lookAheadDummy)

    def _isLeftRecursive_i(self, target, visitedExprIdSet):
        id_self = id(self)
        if id_self in visitedExprIdSet:
            return False
        visitedExprIdSet.add(id_self)
        if isinstance(self.__expr, _UninterpretableNode):
            raise LeftRecursionUndecided(repr(self))
        return self.expr is target or self.expr._isLeftRecursive_i(target, visitedExprIdSet)
