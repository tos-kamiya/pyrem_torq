from pyrem_torq.expression import *

class OperatorBuilder(object):
    def __init__(self, 
            atomicValueExpr=None, 
            composedValueNodeLabels=None, 
            generatedValueLabel=None):
        self.__ave = atomicValueExpr if atomicValueExpr is not None else Never()
        self.__cvnls = composedValueNodeLabels
        self.__gvl = generatedValueLabel
    
    def set_atomic_value_expr(self, atomicValueExpr):
        assert isinstance(atomicValueExpr, TorqExpression)
        self.__ave = atomicValueExpr
    def get_atomic_value_expr(self):
        return self.__ave
    atomic_value_expr = property(get_atomic_value_expr, set_atomic_value_expr)
    
    def set_composed_value_node_labels(self, labels):
        for lbl in labels: assert lbl # is not empty
        self.__cvnls = frozenset(lbl for lbl in labels)
    def get_composed_value_node_labels(self):
        return sorted(self.__cvnls)
    composed_value_node_labels = property(get_composed_value_node_labels, set_composed_value_node_labels)
    
    def set_generated_value_label(self, label): 
        assert label # is not empty string
        self.__gvl = label
    def get_generated_value_label(self, label): return self.__gvl
    generated_value_label = property(get_generated_value_label, set_generated_value_label)
    
    def _make_value_expr(self):
        values = [ self.__ave ]
        values.extend(NodeMatch(lbl, Search(Marker('0'))) for lbl in self.__cvnls)
        return Or.build(*values)
    
    def build_Ov_expr(self, *ops):
        assert self.__ave and self.__cvnls and self.__gvl
        
        signLikeExprs = [] # -123
        castLikeExprs = [] # (int)fvalue
        for op in ops:
            if isinstance(op, TorqExpression):
                signLikeExprs.append(op)
            else:
                opOpen, opClose = op
                castLikeExprs.append(( opOpen, opClose ))
        
        opBeginExprs = []
        opBeginExprs.extend(signLikeExprs)
        opBeginExprs.extend(opOpen for opOpen, opClose in castLikeExprs)
            
        valueExpr = self._make_value_expr()
        
        ovExprs = []
        for opOpen, opClose in castLikeExprs:
            e = opOpen + [0,None] * (Xcp(opClose) + (Marker('0') | Any())) + opClose
            ovExprs.append(e)
        ovExprs.extend(signLikeExprs)
        
        whereShouldNotBeRegardedAsOperator = [0,1] * Or.build(*opBeginExprs)
        expr = BuildToNode(self.__gvl, [1,None] * Or.build(*ovExprs) + valueExpr) + whereShouldNotBeRegardedAsOperator
        # this "+ [0,1] * Or.build(*opBeinExprs)" is used to neglect the operator appears after some value.
        
        expr = expr | (valueExpr + whereShouldNotBeRegardedAsOperator)
        
        assign_marker_expr(expr, '0', expr) 
        return Search(expr)
    
    def build_vO_expr(self, *ops):
        assert self.__ave and self.__cvnls and self.__gvl
        
        repeatLikeExprs = [] # \d+
        callLikeExprs = [] # f(1, 2)
        for op in ops:
            if isinstance(op, TorqExpression):
                repeatLikeExprs.append(op)
            else:
                opOpen, opClose = op
                callLikeExprs.append(( opOpen, opClose ))
        
        valueExpr = self._make_value_expr()
        
        values = [ self.__ave ]
        values.extend(Node(lbl) for lbl in self.__cvnls)
        whereValueShouldNotAppear = Xcp(Or.build(*values))
        
        voExprs = []
        for opOpen, opClose in callLikeExprs:
            e = opOpen + [0,None] * (Xcp(opClose) + (Marker('0') | Any())) + opClose + whereValueShouldNotAppear
            voExprs.append(e)
        for op in repeatLikeExprs:
            e = op + whereValueShouldNotAppear
            voExprs.append(e)
        
        expr = BuildToNode(self.__gvl, valueExpr + [1,None] * Or.build(*voExprs))
        expr = expr | valueExpr
        assign_marker_expr(expr, '0', expr) 
        return Search(expr)
    
    def build_vOv_expr(self, *ops):
        assert self.__ave and self.__cvnls and self.__gvl
        
        addLikeExprs = [] # 1 + 2
        conditionLikeExprs = [] # flag ? 1 : 0
        
        for op in ops:
            if isinstance(op, TorqExpression):
                addLikeExprs.append(op)
            else:
                opOpen, opClose = op
                conditionLikeExprs.append(( opOpen, opClose ))
        
        valueExpr = self._make_value_expr()
        
        vowExprs = []
        for opOpen, opClose in conditionLikeExprs:
            e = opOpen + [0,None] * (Xcp(opClose) + (Marker('0') | Any())) + opClose
            vowExprs.append(e)
        vowExprs.extend(addLikeExprs)
        
        expr = BuildToNode(self.__gvl, valueExpr + [1,None] * (Or.build(*vowExprs) + valueExpr))
        expr = expr | valueExpr
        assign_marker_expr(expr, '0', expr) 
        return Search(expr)
    
    def build_O_expr(self, *ops):
        assert self.__ave and self.__cvnls and self.__gvl
        
        valueExpr = self._make_value_expr()
        
        ovpExprs = []
        for opOpen, opClose in ops:
            e = BuildToNode(self.__gvl, opOpen + [0,None] * (Xcp(opClose) + (Marker('0') | Any())) + opClose)
            ovpExprs.append(e)
        ovpExprs.append(valueExpr)
        expr = Or.build(*ovpExprs)
        expr = expr | valueExpr
        assign_marker_expr(expr, '0', expr) 
        return Search(expr)

if __name__ == '__main__':
    import re
    from pyrem_torq.treeseq import seq_pretty
    
    kit = OperatorBuilder()
    kit.atomic_value_expr = Rex(r"^\d") | Rex(r"^\w")
    kit.composed_value_node_labels = ( "v", )
    kit.generated_value_label = "v"
    
    descAndExprs = []
    descAndExprs.append(( "funcCallExpr", kit.build_vO_expr(( Literal("("), Literal(")") )) ))
    descAndExprs.append(( "parenExpr", kit.build_O_expr(( Literal("("), Literal(")") )) ))
    descAndExprs.append(( "indexExpr", kit.build_vO_expr(( Literal("["), Literal("]") )) ))
    descAndExprs.append(( "unaryMinusExpr", kit.build_Ov_expr(Literal("-")) ))
    descAndExprs.append(( "binaryStarExpr", kit.build_vOv_expr(Literal("*")) ))
    descAndExprs.append(( "binaryMinusExpr", kit.build_vOv_expr(Literal("-")) ))
    descAndExprs.append(( "conditionExpr", kit.build_vOv_expr(( Literal("?"), Literal(":") )) ))
    
    text = "-1-2*(3-4)-a[5]*6?7:8-9?b(c,d):e"
    seq = [ 'code' ] + [m.group() for m in re.finditer(r"[a-z]+|(\d|[.])+|[-+*/%()?:,]|\[|\]", text)]
    for desc, expr in descAndExprs:
        print "step: %s" % desc
        seq = expr.parse(seq)
        assert True
        for L in seq_pretty(seq): print L
