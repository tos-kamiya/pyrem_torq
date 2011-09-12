from base_expression import *

class __S(object):
    __slots__ = [ '__name' ]
    def __init__(self, name): self.__name = name
    def __hash__(self): return hash(self.__name)
    def __eq__(self, right): return self is right
    def __ne__(self, right): return self is not right
    def __repr__(self): return "__S(%s)" % self.__name
FLATTEN = __S('FLATTEN')

class ForbiddenNewLabel(ValueError):
    pass

class Node(TorqExpression):
    ''' Node expression matches to a length-1 sequence of a node whose label is the same to the internal label.
    '''
    
    __slots__ = [ '__label', '__newLabel' ]
        
    def getlabel(self): return self.__label
    label = property(getlabel)
    
    def extract_labels(self): return [ self.__label ]
    
    def getnewlabel(self): return self.__newLabel
    newLabel = property(getnewlabel)
    
    def extract_new_labels(self): 
        return [ self.__newLabel ] if self.__newLabel not in ( None, FLATTEN ) else ()
    
    def __init__(self, label, newLabel=None):
        self.__label = label
        assert newLabel != ''
        self.__newLabel = newLabel
        
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        if lookAheadNode[0] == self.__label:
            if self.__newLabel is FLATTEN:
                nodeContentIter = iter(lookAheadNode); nodeContentIter.next()
                return 1, nodeContentIter, ()
            elif self.__newLabel is None:
                return 1, ( lookAheadNode, ), ()
            else:
                newNode = lookAheadNode[:]; newNode[0] = self.__newLabel
                return 1, ( newNode, ), ()
        #return None
    
    def __eq__(self, right): 
        return isinstance(right, Node) and self.__label == right.label and \
                self.__newLabel == right.newLabel
    
    def __repr__(self): return "Node(%s,newLabel=%s)" % ( repr(self.__label), repr(self.__newLabel) )
    def __hash__(self): return hash("Node") + hash(self.__label) + hash(self.__newLabel)
    
    def required_node_literal_epsilon(self):
        return ( self.__label, ), (), False
            
    def or_merged(self, other):
        if isinstance(other, ( Node, NodeClass, AnyNode )):
            return NodeClass.merged([ self, other ])
        return None
    
    @staticmethod
    def build(label, newLabel=None): return Node(label, newLabel)

class AnyNode(TorqExpression):
    ''' Node expression matches to a length-1 sequence of a node.
    '''
    
    __slots__ = [ '__newLabel' ]
        
    def getnewlabel(self): return self.__newLabel
    newLabel = property(getnewlabel)
    
    def extract_new_labels(self): 
        return [ self.__newLabel ] if self.__newLabel not in ( None, FLATTEN ) else ()
    
    def __init__(self, newLabel=None):
        assert newLabel != ''
        self.__newLabel = newLabel
        
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        if self.__newLabel is FLATTEN:
            nodeContentIter = iter(lookAheadNode); nodeContentIter.next()
            return 1, nodeContentIter, ()
        elif self.__newLabel is None:
            return 1, ( lookAheadNode, ), ()
        else:
            newNode = lookAheadNode[:]; newNode[0] = self.__newLabel
            return 1, ( newNode, ), ()
    
    def __eq__(self, right): 
        return isinstance(right, AnyNode) and self.__newLabel == right.newLabel
    
    def __repr__(self): return "AnyNode(newLabel=%s)" % repr(self.__newLabel)
    def __hash__(self): return hash("AnyNode") + hash(self.__newLabel)
    
    def or_merged(self, other):
        if isinstance(other, ( Node, NodeClass, AnyNode )):
            return NodeClass.merged([ self, other ])
        return None
    
    @staticmethod
    def build(newLabel=None): return AnyNode(newLabel)

class NodeMatch(TorqExpressionWithExpr):
    ''' NodeMatch expression matches to a length-1 sequence of a node iff 
       - the label of the node is the same to the internal label, and 
       - the internal expression matches the node's internal sequence.
    '''
    
    __slots__ = [ '__label', '__newLabel' ]
    
    def getlabel(self): return self.__label
    label = property(getlabel)
    
    def extract_labels(self): return [ self.__label ]
    
    def getnewlabel(self): return self.__newLabel
    newLabel = property(getnewlabel)
    
    def extract_new_labels(self): 
        return [ self.__newLabel ] if self.__newLabel not in ( None, FLATTEN ) else ()
    
    def __init__(self, label, expr, newLabel=None):
        #assert expr is not None # use Node, instead!
        self._set_expr(expr)
        self.__label = label
        assert newLabel != ''
        self.__newLabel = newLabel
        
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
                r = (self._expr._match_node if isinstance(lah, list) else self._expr._match_lit)(lookAheadNode, 1, lah)
        except InterpretError, e:
            e.stack.insert(0, inpPos); raise e
        if r is None: return None
        p, o, d = r
        if 1 + p != len_node: return None
        if self.__newLabel is FLATTEN:
            return 1, o, d
        else:
            newNode = [ lookAheadNode[0] if self.__newLabel is None else self.__newLabel ]
            newNode.extend(o)
            return 1, ( newNode, ), d

    def __eq__(self, right): 
        return isinstance(right, NodeMatch) and self.__label == right.label and \
                self.expr == right.expr and self.__newLabel == right.newLabel
    
    def __repr__(self): return "NodeMatch(%s,%s,newLabel=%s)" % \
            ( repr(self.__label), repr(self.expr), repr(self.__newLabel) )
            
    def __hash__(self): return hash("NodeMatch") + hash(self.expr) + hash(self.__label) + hash(self.__newLabel)

    def required_node_literal_epsilon(self):
        return ( self.__label, ), (), False
            
    @staticmethod
    def build(label, expr, newLabel=None): return NodeMatch(label, expr, newLabel)

class AnyNodeMatch(TorqExpressionWithExpr):
    ''' NodeMatch expression matches to a length-1 sequence of a node iff 
        the internal expression matches the node's internal sequence.
    '''
    
    __slots__ = [ '__newLabel' ]
    
    def getnewlabel(self): return self.__newLabel
    newLabel = property(getnewlabel)
    
    def extract_new_labels(self): 
        return [ self.__newLabel ] if self.__newLabel not in ( None, FLATTEN ) else ()
    
    def __init__(self, expr, newLabel=None):
        #assert expr is not None # use Node, instead!
        self._set_expr(expr)
        assert newLabel != ''
        self.__newLabel = newLabel
        
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        #assert self.expr != None
        len_node = len(lookAheadNode); assert len_node >= 1
        try:
            if len_node == 1:
                r = self._expr._match_eon(lookAheadNode, 1, None)
            else:
                lah = lookAheadNode[1]
                r = (self._expr._match_node if isinstance(lah, list) else self._expr._match_lit)(lookAheadNode, 1, lah)
        except InterpretError, e:
            e.stack.insert(0, inpPos); raise e
        if r is None: return None
        p, o, d = r
        if 1 + p != len_node: return None
        if self.__newLabel is FLATTEN:
            return 1, o, d
        else:
            newNode = [ lookAheadNode[0] if self.__newLabel is None else self.__newLabel ]
            newNode.extend(o)
            return 1, ( newNode, ), d

    def __eq__(self, right): 
        return isinstance(right, AnyNodeMatch) and self.expr == right.expr and \
                self.__newLabel == right.newLabel
    
    def __repr__(self): return "NodeMatch(%s,newLabel=%s)" % \
            ( repr(self.expr), repr(self.__newLabel) )
            
    def __hash__(self): return hash("AnyNodeMatch") + hash(self.expr) + hash(self.__newLabel)

    @staticmethod
    def build(expr, newLabel=None): return AnyNodeMatch(expr, newLabel)

class NodeClass(TorqExpression):
    ''' NodeMatch expression matches to a length-1 sequence of a node whose
        label is the same to one of the internal labels.
    '''
    
    __slots__ = [ '__newLabel', '__labels' ]
    
    def getlabels(self): return sorted(self.__labels)
    labels = property(getlabels)
    
    def extract_labels(self): return sorted(self.__labels)
    
    def getnewlabel(self): return self.__newLabel
    newLabel = property(getnewlabel)
    
    def extract_new_labels(self): 
        return [ self.__newLabel ] if self.__newLabel not in ( None, FLATTEN ) else ()
    
    def __init__(self, labels, newLabel=None):
        self.__labels = frozenset(labels)
        assert newLabel != ''
        self.__newLabel = newLabel
        
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        if lookAheadNode[0] in self.__labels:
            if self.__newLabel is FLATTEN:
                nodeContentIter = iter(lookAheadNode); nodeContentIter.next()
                return 1, nodeContentIter, ()
            elif self.__newLabel is None:
                return 1, ( lookAheadNode, ), ()
            else:
                newNode = lookAheadNode[:]; newNode[0] = self.__newLabel
                return 1, ( newNode, ), ()
        #return None
    
    def __eq__(self, right): 
        return isinstance(right, NodeClass) and self.__labels == right.__labels and \
                self.__newLabel == right.newLabel
    
    def __repr__(self): return "NodeClass([%s],newLabel=%s)" % ( ",".join(repr(lbl) for lbl in sorted(self.__labels)), repr(self.__newLabel) )
    def __hash__(self): return hash("NodeClass") + sum(map(hash, self.__labels)) + hash(self.__newLabel)
    
    def required_node_literal_epsilon(self):
        return tuple(sorted(self.__labels)), (), False
            
    def or_merged(self, other):
        if isinstance(other, ( Node, NodeClass, AnyNode )):
            return NodeClass.merged([ self, other ])
        return None

    @staticmethod
    def merged(nodeExprOrNodeClasss):
        if not nodeExprOrNodeClasss: return None
        theNewLabel = nodeExprOrNodeClasss[0].newLabel
        for item in nodeExprOrNodeClasss[1:]:
            if item.newLabel != theNewLabel:
                return None
        
        labelSet = set()
        for item in nodeExprOrNodeClasss:
            if isinstance(item, AnyNode):
                return AnyNode.build(newLabel=theNewLabel)
            if isinstance(item, Node):
                labelSet.add(item.label)
            elif isinstance(item, NodeClass):
                labelSet.update(item.__labels)
        return NodeClass.build(labelSet, newLabel=theNewLabel)

    @staticmethod
    def build(labels, newLabel=None): return NodeClass(labels, newLabel)

class InsertNode(TorqExpression):
    ''' InsertNode expression always matches, and inserts a node having the label at the
        current position in the output sequence.
    '''
    
    __slots__ = [ '__newLabel' ]
    
    def getnewlabel(self): return self.__newLabel
    newLabel = property(getnewlabel)
    
    def extract_new_labels(self): return [ self.__newLabel ]
    
    def __init__(self, newLabel):
        assert newLabel not in ( None, '', FLATTEN )
        self.__newLabel = newLabel
    
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        return 0, ( [ self.__newLabel ], ), ()
    _match_lit = _match_eon = _match_node
    
    def required_node_literal_epsilon(self):
        return (), (), True
            
    def __eq__(self, right): 
        return isinstance(right, InsertNode) and self.__newLabel == right.newLabel
    
    def __repr__(self): return "InsertNode(%s)" % repr(self.__newLabel) 
    def __hash__(self): return hash("InsertNode") + hash(self.__newLabel)

    @staticmethod
    def build(newLabel): return InsertNode(newLabel)

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
        assert newLabel not in ( None, '', FLATTEN )
        self.__newLabel = newLabel
    
    def __make_return_value(self, r):
        if r is None: return None
        p, o, d = r
        newNode = [ self.__newLabel ]
        newNode.extend(o)
        return p, ( newNode, ), d
    
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        return self.__make_return_value(self._expr._match_node(inpSeq, inpPos, lookAheadNode))
    
    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        return self.__make_return_value(self._expr._match_lit(inpSeq, inpPos, lookAheadString))
    
    def _match_eon(self, inpSeq, inpPos, lookAheadDummy):
        return self.__make_return_value(self._expr._match_eon(inpSeq, inpPos, lookAheadDummy))
    
    def __eq__(self, right): 
        return isinstance(right, BuildToNode) and self.__newLabel == right.newLabel and \
                self.expr == right.expr
    
    def __repr__(self): return "BuildToNode(%s,%s)" % (repr(self.__newLabel), repr(self.expr) )
    def __hash__(self): return hash("BuildToNode") + hash(self.__newLabel) + hash(self.expr)

    def required_node_literal_epsilon(self):
        return self.expr.required_node_literal_epsilon()
            
    @staticmethod
    def build(newLabel, expr): 
        if isinstance(expr, Epsilon):
            return InsertNode(newLabel)
        elif isinstance(expr, Never):
            return expr
        elif isinstance(expr, Node) and expr.newLabel is FLATTEN:
            return Node(expr.label, newLabel=newLabel)
        elif isinstance(expr, NodeMatch) and expr.newLabel is FLATTEN:
            return NodeMatch(expr.label, expr.expr, newLabel=newLabel)
        elif isinstance(expr, AnyNode) and expr.newLabel is FLATTEN:
            return AnyNode(newLabel=newLabel)
        elif isinstance(expr, NodeClass) and expr.newLabel is FLATTEN:
            return NodeClass(expr.labels, newLabel=newLabel)
        return BuildToNode(newLabel, expr)

class Drop(TorqExpressionWithExpr):
    ''' Drop expression matches to a sequence which the internal expression matches.
       When matches, appends the matched sequence the current dropped sequence.
    '''
    
    __slots__ = [ ]
    
    def __init__(self, expr):
        self._set_expr(expr)
    
    @staticmethod
    def __make_return_value(r):
        if r is None: return None
        p, o, d = r
        if not d: return p, (), o
        if not o: return p, (), d
        dropSeq = d if isinstance(d, list) else list(d)
        dropSeq.extend(o)
        return p, (), dropSeq
    
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        return Drop.__make_return_value(self._expr._match_node(inpSeq, inpPos, lookAheadNode))
    
    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        return Drop.__make_return_value(self._expr._match_lit(inpSeq, inpPos, lookAheadString))
    
    def _match_eon(self, inpSeq, inpPos, lookAheadDummy):
        return Drop.__make_return_value(self._expr._match_eon(inpSeq, inpPos, lookAheadDummy))
    
    def required_node_literal_epsilon(self):
        return self.expr.required_node_literal_epsilon()
            
    @staticmethod
    def build(expr): 
        if isinstance(expr, ( Epsilon, Never )):
            return expr
        return Drop(expr)
