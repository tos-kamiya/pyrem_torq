#coding: utf-8

from base_expression import TorqExpression, InterpretError, LeftRecursionUndecided


class _UninterpretableNode(TorqExpression):
    __slots__ = ['__raise_error']

    def __init__(self, raise_error):
        self.__raise_error = raise_error
    
    def _match_node(self, inpSeq, inpPos, lookAheadNode): self.__raise_error(inpPos)
    _match_lit = _match_eon = _match_node

class Holder(TorqExpression):
    ''' A special expression, which is used as a place holder of an expression.
        A Holder object has two properties: name and expr.
        The name property is a label of the object.
        The expr property is an internal expression of the object.
        When evaluated an expression, the object behaves as if it were the internal expression.
        If no internal expression is set, the object raises InterpreterError.
    '''

    __slots__ = ['__name', '__expr', '__mc4la']

    def __init__(self, name=None):
        self.__name = name
        self.__expr = _UninterpretableNode(self.__raise_error)
        self.__mc4la = None
    
    def __repr__(self): return "Holder(name=%s)" % repr(self.__name)

    def __hash__(self): return hash("Holder") + hash(self.__name)

    def _eq_i(self, right, alreadyComparedExprs):
        if right.__class__ is not Holder: return False
        if self.__name != right.__name: return False
        if (id(self), id(right), True) in alreadyComparedExprs:
            return True
        alreadyComparedExprs.add((id(self), id(right), True))  # now self and right is under comparision...
        r = self.__expr._eq_i(right.__expr, alreadyComparedExprs)
        if not r:
            alreadyComparedExprs.add((id(self), id(right), False))  # now found self doesn't equal to right
        return r
        
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

    def extract_exprs(self): return [self.__expr]

    def extract_labels(self):
        return self.__expr.extract_labels() if hasattr(self.__expr, "extract_labels") else []
    
    def extract_new_labels(self):
        return self.__expr.extract_new_labels() if hasattr(self.__expr, "extract_new_labels") else []
    
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
