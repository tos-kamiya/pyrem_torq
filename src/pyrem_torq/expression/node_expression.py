from base_expression import *

class EnsuredAcceptSingleNode: pass
class NodeModifier: pass

class Relabeled(TorqExpressionWithExpr, NodeModifier):
    __slots__ = [ '__newLabel' ]
    
    def __init__(self, newLabel, nodeExpr):
        assert not isinstance(nodeExpr, NodeModifier)
        assert isinstance(nodeExpr, EnsuredAcceptSingleNode)
        assert newLabel
        self.__newLabel = newLabel
        self._set_expr(nodeExpr)

    def getnewlabel(self): return self.__newLabel
    newLabel = property(getnewlabel)
    
    def extract_new_labels(self): 
        return [ self.__newLabel ]
    
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        r = self._expr._match_node(inpSeq, inpPos, lookAheadNode)
        if r is not None:
            p, o = r
            assert p == 1
            newNode = o[0]
            if not isinstance(newNode, list): newNode = list(newNode)
            newNode[0] = self.__newLabel
            return p, ( newNode, )

    def _eq_i(self, right, alreadyComparedExprs):
        return right.__class__ is Relabeled and self.expr._eq_i(right.expr, alreadyComparedExprs) and \
                self.__newLabel == right.__newLabel
    
    def __repr__(self): return "Relabeled(%s,%s)" % ( repr(self.__newLabel), repr(self.expr) )
    def __hash__(self): return hash("Relabeled") + hash(self.__newLabel) + hash(self.expr)
    
    def getMatchCandidateForLookAhead(self): return self._expr.getMatchCandidateForLookAhead()
    
    def optimized(self, objectpool={}):
        e = self.expr.optimized(objectpool)
        if hash(e) in objectpool:
            return optimize_simple_expr(self, objectpool)
        if e is not self.expr:
            return Relabeled(self.__newLabel, e)
        return self
    
    def _isLeftRecursive_i(self, target, visitedExprIdSet):
        return self.expr._isLeftRecursive_i(target, visitedExprIdSet)
            
class Flattened(TorqExpressionWithExpr, NodeModifier):
    __slots__ = [ ]
    
    def __init__(self, nodeExpr):
        assert not isinstance(nodeExpr, NodeModifier)
        assert isinstance(nodeExpr, EnsuredAcceptSingleNode)
        self._set_expr(nodeExpr)

    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        r = self._expr._match_node(inpSeq, inpPos, lookAheadNode)
        if r is not None:
            p, o = r
            assert p == 1
            nodeContentIter = iter(o[0]); nodeContentIter.next()
            return p, nodeContentIter
        
    def _eq_i(self, right, alreadyComparedExprs):
        return right.__class__ is Flattened and self.expr._eq_i(right.expr, alreadyComparedExprs)
    
    def __repr__(self): return "Flattened(%s)" % repr(self.expr)
    def __hash__(self): return hash("Flattened") + hash(self.expr)
    
    def getMatchCandidateForLookAhead(self): return self.expr.getMatchCandidateForLookAhead()
    
    def optimized(self, objectpool={}):
        if isinstance(self.expr, Node):
            return _FlattenedNode(self.expr.label).optimized(objectpool)
        e = self.expr.optimized(objectpool)
        if hash(e) in objectpool:
            return optimize_simple_expr(self, objectpool)
        if e is not self.expr:
            return Flattened(e)
        return self
    
    def _isLeftRecursive_i(self, target, visitedExprIdSet):
        return self.expr._isLeftRecursive_i(target, visitedExprIdSet)
            
class _FlattenedNode(TorqExpressionWithExpr):
    __slots__ = [ '__label', '__mc4la' ]
        
    def getlabel(self): return self.__label
    label = property(getlabel)
    
    def extract_labels(self): return [ self.__label ]
    
    def __init__(self, label):
        self.__label = label
        self.__mc4la = MatchCandidateForLookAhead(nodes=( self.__label, ))
        
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        if lookAheadNode[0] == self.__label:
            nodeContentIter = iter(lookAheadNode); nodeContentIter.next()
            return 1, nodeContentIter
        #return None
    
    def _eq_i(self, right, alreadyComparedExprs):
        return right.__class__ is _FlattenedNode and self.__label == right.label
    
    def __repr__(self): return "_FlattenedNode(%s)" % repr(self.__label)
    def __hash__(self): return hash("_FlattenedNode") + hash(self.__label)
    
    def getMatchCandidateForLookAhead(self): return self.__mc4la
            
    def optimized(self, objectpool={}):
        return optimize_simple_expr(self, objectpool)
            
class Node(TorqExpression, EnsuredAcceptSingleNode):
    ''' Node expression matches to a length-1 sequence of a node whose label is the same to the internal label.
    '''
    
    __slots__ = [ '__label', '__mc4la' ]
        
    def getlabel(self): return self.__label
    label = property(getlabel)
    
    def extract_labels(self): return [ self.__label ]
    
    def __init__(self, label):
        self.__label = label
        self.__mc4la = MatchCandidateForLookAhead(nodes=( self.__label, ))
        
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        if lookAheadNode[0] == self.__label:
            return 1, ( lookAheadNode, )
        #return None
    
    def _eq_i(self, right, alreadyComparedExprs):
        return right.__class__ is Node and self.__label == right.label
    
    def __repr__(self): return "Node(%s)" % repr(self.__label)
    def __hash__(self): return hash("Node") + hash(self.__label)
    
    def getMatchCandidateForLookAhead(self): return self.__mc4la
            
    def or_merged(self, other):
        if other.__class__ is Node or other.__class__ is NodeClass or other.__class__ is AnyNode:
            return NodeClass.merged([ self, other ])
        return None

    def optimized(self, objectpool={}):
        return optimize_simple_expr(self, objectpool)

_anyNodeMc4la = MatchCandidateForLookAhead(nodes=None)

class AnyNode(TorqExpressionSingleton, EnsuredAcceptSingleNode):
    ''' Node expression matches to a length-1 sequence of a node.
    '''
    
    __slots__ = [ ]
        
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        return 1, ( lookAheadNode, )
    
    def __repr__(self): return "AnyNode()"
    def __hash__(self): return hash("AnyNode")
    
    def getMatchCandidateForLookAhead(self): return _anyNodeMc4la
            
    def or_merged(self, other):
        if other.__class__ is Node or other.__class__ is NodeClass or other.__class__ is AnyNode:
            return NodeClass.merged([ self, other ])
        return None
    
class NodeMatch(TorqExpressionWithExpr, EnsuredAcceptSingleNode):
    ''' NodeMatch expression matches to a length-1 sequence of a node iff 
       - the label of the node is the same to the internal label, and 
       - the internal expression matches the node's internal sequence.
    '''
    
    __slots__ = [ '__label', '__mc4la' ]
    
    def getlabel(self): return self.__label
    label = property(getlabel)
    
    def extract_labels(self): return [ self.__label ]
    
    def __init__(self, label, expr):
        #assert expr is not None # use Node, instead!
        self._set_expr(expr)
        self.__label = label
        self.__mc4la = MatchCandidateForLookAhead(nodes=( self.__label, ))
        
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        #assert self.expr != None
        if lookAheadNode[0] != self.__label: 
            return None
        len_node = len(lookAheadNode); assert len_node >= 1
        try:
            if len_node == 1:
                r = self._expr._match_eon(lookAheadNode, 1, None)
            else:
                lah = lookAheadNode[1]
                if lah.__class__ is list:
                    r = self._expr._match_node(lookAheadNode, 1, lah)
                else:
                    #assert lah.__class__ is int #debug
                    r = self._expr._match_lit(lookAheadNode, 1, ( lah, lookAheadNode[2] ))
        except InterpretError, e:
            e.stack.insert(0, inpPos); raise e
        if r is None: return None
        if 1 + r[0] != len_node: return None
        newNode = [ lookAheadNode[0] ]
        newNode.extend(r[1])
        return 1, ( newNode, )

    def _eq_i(self, right, alreadyComparedExprs):
        return right.__class__ is NodeMatch and self.__label == right.label and self.expr._eq_i(right.expr, alreadyComparedExprs)
    
    def __repr__(self): return "NodeMatch(%s,%s)" % \
            ( repr(self.__label), repr(self.expr) )
            
    def __hash__(self): return hash("NodeMatch") + hash(self.expr) + hash(self.__label)

    def getMatchCandidateForLookAhead(self): return self.__mc4la
            
    def optimized(self, objectpool={}):
        optimizedExpr = self.expr.optimized(objectpool)
        if hash(optimizedExpr) in objectpool:
            return optimize_simple_expr(self, objectpool)
        if optimizedExpr is not self.expr:
            return NodeMatch(self.__label, self.expr)
        return self

class AnyNodeMatch(TorqExpressionWithExpr, EnsuredAcceptSingleNode):
    ''' NodeMatch expression matches to a length-1 sequence of a node iff 
        the internal expression matches the node's internal sequence.
    '''
    
    __slots__ = [ ]
    
    def __init__(self, expr):
        #assert expr is not None # use Node, instead!
        self._set_expr(expr)
        
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        #assert self.expr != None
        len_node = len(lookAheadNode); assert len_node >= 1
        try:
            if len_node == 1:
                r = self._expr._match_eon(lookAheadNode, 1, None)
            else:
                lah = lookAheadNode[1]
                if lah.__class__ is list:
                    r = self._expr._match_node(lookAheadNode, 1, lah)
                else:
                    #assert lah.__class__ is int #debug
                    r = self._expr._match_lit(lookAheadNode, 1, ( lah, lookAheadNode[2] ))
        except InterpretError, e:
            e.stack.insert(0, inpPos); raise e
        if r is None: return None
        if 1 + r[0] != len_node: return None
        newNode = [ lookAheadNode[0] ]
        newNode.extend(r[1])
        return 1, ( newNode, )

    def _eq_i(self, right, alreadyComparedExprs):
        return right.__class__ is AnyNodeMatch and self.expr._eq_i(right.expr, alreadyComparedExprs)
    
    def __repr__(self): return "NodeMatch(%s)" % repr(self.expr)
            
    def __hash__(self): return hash("AnyNodeMatch") + hash(self.expr)

    def getMatchCandidateForLookAhead(self): return _anyNodeMc4la
            
    def optimized(self, objectpool={}):
        optimizedExpr = self.expr.optimized(objectpool)
        if hash(optimizedExpr) in objectpool:
            return optimize_simple_expr(self, objectpool)
        if optimizedExpr is not self.expr:
            return AnyNodeMatch(self.expr, newLabel=self.__newLabel)
        return self

class NodeClass(TorqExpression, EnsuredAcceptSingleNode):
    ''' NodeMatch expression matches to a length-1 sequence of a node whose
        label is the same to one of the internal labels.
    '''
    
    __slots__ = [ '__labels', '__mc4la' ]
    
    def getlabels(self): return sorted(self.__labels)
    labels = property(getlabels)
    
    def extract_labels(self): return sorted(self.__labels)
    
    def __init__(self, labels):
        self.__labels = frozenset(labels)
        self.__mc4la = MatchCandidateForLookAhead(nodes=sorted(self.__labels))
        
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        if lookAheadNode[0] in self.__labels:
            return 1, ( lookAheadNode, )
        #return None
    
    def _eq_i(self, right, alreadyComparedExprs):
        return right.__class__ is NodeClass and self.__labels == right.__labels
    
    def __repr__(self): return "NodeClass([%s])" % ",".join(repr(lbl) for lbl in sorted(self.__labels))
    def __hash__(self): return hash("NodeClass") + sum(map(hash, self.__labels))
    
    def getMatchCandidateForLookAhead(self): return self.__mc4la
            
    def or_merged(self, other):
        if other.__class__ is Node or other.__class__ is NodeClass or other.__class__ is AnyNode:
            return NodeClass.merged([ self, other ])
        return None

    @staticmethod
    def merged(nodeExprOrNodeClasss):
        if not nodeExprOrNodeClasss: return None
        
        labelSet = set()
        for item in nodeExprOrNodeClasss:
            if item.__class__ is AnyNode:
                return AnyNode()
            if item.__class__ is Node:
                labelSet.add(item.label)
            elif item.__class__ is NodeClass:
                labelSet.update(item.__labels)
        return NodeClass(labelSet)

    def optimized(self, objectpool={}):
        return optimize_simple_expr(self, objectpool)

_insertingMc4la = MatchCandidateForLookAhead(nodes=None, literals=None, emptyseq=True)

class InsertNode(TorqExpression):
    ''' InsertNode(label) is equivalent to BuildToNode(label, Epsilon()).
    '''
    
    __slots__ = [ '__newLabel' ]
    
    def getnewlabel(self): return self.__newLabel
    newLabel = property(getnewlabel)
    
    def extract_new_labels(self): return [ self.__newLabel ]
    
    def __init__(self, newLabel):
        assert newLabel
        self.__newLabel = newLabel
    
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        return 0, ( [ self.__newLabel ], )
    _match_lit = _match_eon = _match_node
    
    def getMatchCandidateForLookAhead(self): return _insertingMc4la
            
    def _eq_i(self, right, alreadyComparedExprs):
        return right.__class__ is InsertNode and self.__newLabel == right.newLabel
    
    def __repr__(self): return "InsertNode(%s)" % repr(self.__newLabel) 
    def __hash__(self): return hash("InsertNode") + hash(self.__newLabel)

    def optimized(self, objectpool={}):
        return optimize_simple_expr(self, objectpool)

class BuildToNode(TorqExpressionWithExpr):
    ''' BuildToNode expression matches to a sequence which the internal expression matches.
       When matches, inserts a node at the current position in the output sequence and
       makes the matched sequence to internal sequence of the inserted node. 
    '''
    
    __slots__ = [ '__newLabel' ]
    
    def getnewlabel(self): return self.__newLabel
    newLabel = property(getnewlabel)
    
    def extract_new_labels(self): return [ self.__newLabel ]
    
    def __init__(self, newLabel, expr):
        #assert expr is not None # use Node, instead!
        self._set_expr(expr)
        assert newLabel
        self.__newLabel = newLabel
    
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        r = self._expr._match_node(inpSeq, inpPos, lookAheadNode)
        if r:
            newNode = [ self.__newLabel ]; newNode.extend(r[1])
            return r[0], ( newNode, )
    
    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        r = self._expr._match_lit(inpSeq, inpPos, lookAheadString)
        if r:
            newNode = [ self.__newLabel ]; newNode.extend(r[1])
            return r[0], ( newNode, )
    
    def _match_eon(self, inpSeq, inpPos, lookAheadDummy):
        r = self._expr._match_eon(inpSeq, inpPos, lookAheadDummy)
        if r:
            newNode = [ self.__newLabel ]; newNode.extend(r[1])
            return r[0], ( newNode, )
    
    def _eq_i(self, right, alreadyComparedExprs):
        return right.__class__ is BuildToNode and self.__newLabel == right.__newLabel and \
                self.expr._eq_i(right.expr, alreadyComparedExprs)
    
    def __repr__(self): return "BuildToNode(%s,%s)" % (repr(self.__newLabel), repr(self.expr) )
    def __hash__(self): return hash("BuildToNode") + hash(self.__newLabel) + hash(self.expr)

    def getMatchCandidateForLookAhead(self): 
        return self.expr.getMatchCandidateForLookAhead()
            
    def optimized(self, objectpool={}):
        if self.expr.__class__ is Epsilon:
            return InsertNode(self.__newLabel).optimized(objectpool)
        optimizedExpr = self.expr.optimized(objectpool)
        if hash(optimizedExpr) in objectpool:
            return optimize_simple_expr(self, objectpool)
        if optimizedExpr is not self.expr:
            return BuildToNode(self.__newLabel, optimizedExpr)
        return self

    def _isLeftRecursive_i(self, target, visitedExprIdSet):
        id_self = id(self)
        if id_self in visitedExprIdSet:
            return False
        visitedExprIdSet.add(id_self)
        return self.expr is target or self.expr._isLeftRecursive_i(target, visitedExprIdSet)
            
