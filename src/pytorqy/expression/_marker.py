from ._expression import *

class Marker(TorqExpression):
    __slots__ = [ '__name', '__expr' ]
    
    def __init__(self, name):
        self.__name = name
        self.__expr = None
    
    def __eq__(self, right): 
        return id(self) == id(right)
        # Note: this comparison is object-id equivalence, not value equivalence.
        # Because Marker object is used to represent a recursive expression,
        # we have to avoid infinite recursion in some way.
    
    def __repr__(self): return "Marker(%s)" % repr(self.__name)
    def __hash__(self): return hash("Marker") + hash(self.__name)
    
    def getname(self): return self.__name
    def setname(self, name):
        self.__name = name
    name = property(getname, setname, None)
    
    def getexpr(self): return self.__expr
    def setexpr(self, expr):
        if expr is None:
            self.__expr = None
        elif isinstance(expr, TorqExpression):
            self.__expr = expr
        else:
            raise TypeError("Marker.setexpr()'s argument must be an TorqExpression")
    expr = property(getexpr, setexpr, None)
    
    def expr_iter(self):
        yield self.__expr
        
    def __raise_error(self, inpPos):
        e = InterpretError("Interpreting Marker w/o valid expression: '%s'" % self.__name)
        e.stack.insert(0, inpPos)
        raise e
    
    def _match_node(self, inpSeq, inpPos, lookAheadNode):
        if self.__expr is None: self.__raise_error(inpPos)
        return self.__expr._match_node(inpSeq, inpPos, lookAheadNode)
    
    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        if self.__expr is None: self.__raise_error(inpPos)
        return self.__expr._match_lit(inpSeq, inpPos, lookAheadString)

    def _match_eon(self, inpSeq, inpPos, lookAheadDummy):
        if self.__expr is None: self.__raise_error(inpPos)
        return self.__expr._match_eon(inpSeq, inpPos, lookAheadDummy)

    @staticmethod
    def build(name): return Marker(name)

_isMarker = Marker.__instancecheck__

def inner_expr_iter(expr):
    visitedExprIDSet = set()
    def iei_i(e):
        if _isMarker(e):
            ide = id(e)
            if ide in visitedExprIDSet: return # prevent infinite recursion
            visitedExprIDSet.add(ide)
        for item in e.expr_iter():
            if item is not None:
                yield item
                for v in iei_i(item): yield v
    return iei_i(expr)

def inner_marker_iter(expr):
    for e in inner_expr_iter(expr):
        if _isMarker(e):
            yield e

def __lookup_replaces(expr, *args):
    if len(args) == 2:
        marker, replacementExpr = args
        targetName = marker.name if _isMarker(marker) else marker
        tbl = { targetName : replacementExpr }
    else:
        assert len(args) == 1
        tbl = args[0]
    assert isinstance(tbl, dict)
    
    replaceTable = dict(( marker, replacementExpr ) for marker, replacementExpr in tbl.items()) 
    targetMarkers = [e for e in inner_expr_iter(expr) if _isMarker(e) and e.name in replaceTable]
    return replaceTable, targetMarkers

def assign_marker_expr(expr, *args):
    replaceTable, targetMarkers = __lookup_replaces(expr, *args)
    replacedMarkers = []        
    for e in targetMarkers:
        if e.expr is not None: continue
        e.expr = replaceTable[e.name]
        replacedMarkers.append(e)
    return replacedMarkers
    
def update_marker_expr(expr, *args):
    replaceTable, targetMarkers = __lookup_replaces(expr, *args)
    replacedMarkers = []        
    for e in targetMarkers:
        e.expr = replaceTable[e.name]
        replacedMarkers.append(e)
    return replacedMarkers

def free_marker_iter(expr):
    for e in inner_expr_iter(expr):
        if _isMarker(e) and e.expr is None:
            yield e

def extract_redundant_inners(expr):
    innerNodeGroups = {}
    for e in inner_expr_iter(expr):
        innerNodeGroups.setdefault(hash(e), list()).append(e)
    redundantExprs = []
    for g in innerNodeGroups.values():
        uniqExprs = []
        for e in g:
            if len([ue for ue in uniqExprs if ue == e]) == 0:
                uniqExprs.append(e)
            else:
                redundantExprs.append(e)
    return redundantExprs

_notGiven = object()

class ItemOverwriteError(KeyError): pass

class ExprDict(dict):
    def set_silent_overwrite(self, permitOverwrite):
        self.__permitOverwrite = permitOverwrite
    
    def replace_marker_expr(self, expr):
        for m in inner_marker_iter(expr):
            e = self.__markerTbl.get(m.name)
            if e is not None:
                m.expr = e
        return expr
        
    def free_marker_iter(self):
        for _, ms in self.__markerTbl.items():
            for m in ms:
                if m.expr is None:
                    yield m
        
    def __update_markers(self, changedItemTbl):
        for k, v in changedItemTbl.items():
            if v is not None:
                self.__markerTbl[k] = [e for e in inner_expr_iter(v) if _isMarker(e)]
            else:
                self.__markerTbl[k] = []
        for k, ms in self.__markerTbl.items():
            for m in ms:
                e = changedItemTbl.get(m.name)
                if e:
                    m.expr = e
    
    def __init__(self, *args):
        self.__permitOverwrite = True
        self.__markerTbl = {}
        dict.__init__(self, args)
        self.__update_markers(self)
    
    def __delitem__(self, name):
        dict.__delitem__(self, name)
        self.__update_markers({ name : None })
    
    def __setitem__(self, name, expr):
        if not self.__permitOverwrite:
            if name in self: raise ItemOverwriteError("Item already exists for key: %s" % name)
        dict.__setitem__(self, name, expr)
        self.__update_markers({ name : expr })
    
    def update(self, items):
        changedItems = dict(items)
        for name in changedItems.keys():
            if not self.__permitOverwrite:
                if name in self: raise ItemOverwriteError("Item already exists for key: %s" % name)
        dict.update(self, changedItems)
        self.__update_markers(changedItems)
    
    def popitem(self):
        k, v = self.popitem()
        self.__update_markers({ k : None })
        return k, v
        
    def pop(self, k, default=_notGiven):
        try:
            v = dict.pop(self, k)
        except KeyError:
            if default is _notGiven:
                raise
            return default
        else:
            self.__update_markers(self, { k : None })
            return v