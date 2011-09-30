from base_expression import TorqExpressionWithExpr

class SubApply(TorqExpressionWithExpr):
    ''' Applies a given (Python) function to a (sub-)sequence, to which a given expr matches. 
        In the result of parsing, the sub-sequence is replaced with a return value of the function.
    '''
    __slots__ = [ '__func', '__labels', '__newLabels' ]
    
    def __init__(self, func, expr, new_labels=None, labels=None):
        self.__func = func
        self._set_expr(expr)
        referringLabels = []
        if hasattr(expr, "extract_labels"): referringLabels.extend(expr.extract_labels())
        if labels: referringLabels.extend(labels)
        self.__labels = tuple(sorted(referringLabels))
        newLabels = []
        if hasattr(expr, "extract_new_labels"): newLabels.extend(expr.extract_new_labels())
        if new_labels: newLabels.extend(new_labels)
        self.__newLabels = tuple(sorted(newLabels))
        
    def extract_labels(self): return list(self.__labels)
    def extract_new_labels(self): return list(self.__newLabels)
    
    def __modify_output(self, r):
        if r is not None:
            p, o = r
            if o.__class__ is not list:
                o = list(o)
            modifiedO = self.__func(o)
            if modifiedO is None:
                return None
            return p, modifiedO
        
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        return self.__modify_output(self._expr._match_node(inpSeq, inpPos, lookAheadNode))
    
    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        return self.__modify_output(self._expr._match_lit(inpSeq, inpPos, lookAheadString))

    def _match_eon(self, inpSeq, inpPos, lookAheadDummy):
        return self.__modify_output(self._expr._match_eon(inpSeq, inpPos, lookAheadDummy))
    
    def _eq_i(self, right, alreadyComparedExprs):
        return right.__class__ is SubApply and self.expr._eq_i(right.expr, alreadyComparedExprs) and \
                self.__func is right.__func
        # be careful. equality of functions is determined by reference, not by value,
        # when two SubApply objects are compared with method __eq__.
    
    def __repr__(self): return "SubApply(%s,%s)" % ( repr(self.__func), repr(self.expr) )
    def __hash__(self): return hash("SubApply") + hash(self.__func) + hash(self.expr)
    
    def getMatchCandidateForLookAhead(self): return self._expr.getMatchCandidateForLookAhead()
    def updateMatchCandidateForLookAhead(self): return self._expr.updateMatchCandidateForLookAhead()

    def _isLeftRecursive_i(self, target, visitedExprIdSet):
        return self.expr._isLeftRecursive_i(target, visitedExprIdSet)
