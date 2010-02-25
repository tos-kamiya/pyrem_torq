from pytorqy.expression import *

class OperatorKit(object):
    def __init__(self):
        self.__vl = 'value'
        self.__nve = Never()
    
    def set_value_label(self, label): self.__vl = label
    def get_value_label(self, label): return self.__vl
    value_label = property(get_value_label, set_value_label)
    
    def set_nonvalue_expr(self, nonvalueExpr): self.__nve = nonvalueExpr
    def get_nonvalue_expr(self, nonvalueExpr): self.__nve = nonvalueExpr
    nonvalue_expr = property(get_nonvalue_expr, set_nonvalue_expr)
        
    def build_ov_expr(self, *ops):
        vl = self.__vl
        op = Or.build(*ops)
        nonValue = Or.build(op, self.__nve)
        value = NodeMatch(vl, Search(Marker('0'))) | XcpThenAny(nonValue)
        OV = BuildToNode(vl, [1,None] * op + value) + [0,1] * op
        expr = [0,1] * (OV | nonValue) + [0,None] * ((value + [0,1] * op) | OV | nonValue)
        # the "+ [0,1]*op" will neglect the operator when it is uses as a binary operator.
        
        assign_marker_expr(expr, '0', expr) 
        return expr
    
    def build_vo_expr(self, *ops):
        vl = self.__vl
        op = Or.build(*ops)
        nonValue = Or.build(op, self.__nve)
        value = NodeMatch(vl, Search(Marker('0'))) | XcpThenAny(nonValue)
        expr = self.__ntfy, BuildToNode(vl, value + [1,None] * op)
        assign_marker_expr(expr, '0', expr) 
        return Search(expr)
    
    def build_vow_expr(self, *ops):
        vl = self.__vl
        op = Or.build(*ops)
        nonValue = Or.build(op, self.__nve)
        value = NodeMatch(vl, Search(Marker('0'))) | XcpThenAny(nonValue)
        expr = BuildToNode(vl, value + [1,None] * (op + value))
        assign_marker_expr(expr, '0', expr) 
        return Search(expr)
    
    def build_vowp_expr(self, *opPairs):
        vl = self.__vl
        allOps = []
        for opPair in opPairs: allOps.extend(opPair)
        anyOp = Or.build(*allOps)
        nonValue = Or.build(anyOp, self.__nve)
        value = NodeMatch(vl, Search(Marker('0'))) | XcpThenAny(nonValue)
        exprs = [BuildToNode(vl, (value + [1,None] * (opOpen + [0,None] * (value | XcpThenAny(anyOp)) + opClose))) \
            for opOpen, opClose in opPairs]
        expr = Or.build(*exprs)
        assign_marker_expr(expr, '0', expr) 
        return Search(expr)
    
    def build_vowpx_expr(self, *opPairs):
        vl = self.__vl
        allOps = []
        for opPair in opPairs: allOps.extend(opPair)
        anyOp = Or.build(*allOps)
        nonValue = Or.build(anyOp, self.__nve)
        value = NodeMatch(vl, Search(Marker('0'))) | XcpThenAny(nonValue)
        exprs = [BuildToNode(vl, (value + [1,None] * (opOpen + [0,None] * (value | XcpThenAny(anyOp)) + opClose + value))) \
            for opOpen, opClose in opPairs]
        expr = Or.build(*exprs)
        assign_marker_expr(expr, '0', expr) 
        return Search(expr)
    
    def build_ovp_expr(self, parenOpen, parenClose):
        vl = self.__vl
        anyParen = Or(parenOpen, parenClose)
        expr = BuildToNode(vl, parenOpen + [0,None] * Marker('0') + parenClose) | \
            NodeMatch(vl, Search(Marker('0'))) | XcpThenAny(anyParen)
        assign_marker_expr(expr, '0', expr) 
        return Search(expr)

if __name__ == '__main__':
    import re
    from pytorqy.treeseq import seq_pretty
    
    kit = OperatorKit()
    kit.value_label = "v"
    kit.nonvalue_expr = LiteralClass("(),[]-*-?:")
    
    atomExpr = Search(BuildToNode("v", Rex(r"^\d") | Rex(r"^\w")))
    funcCallExpr = kit.build_vowp_expr(( Literal("("), Literal(")") ))
    parenExpr = kit.build_ovp_expr(Literal("("), Literal(")"))
    indexExpr = kit.build_vowp_expr(( Literal("["), Literal("]") ))
    unaryMinusExpr = kit.build_ov_expr(Literal("-"))
    binaryStarExpr = kit.build_vow_expr(Literal("*"))
    binaryMinusExpr = kit.build_vow_expr(Literal("-"))
    conditionExpr = kit.build_vowpx_expr(( Literal("?"), Literal(":") ))
    
    text = "-1-2*(3-4)*a[5]*6?7:8-9?b(c,d):e"
    seq = [ 'code' ] + [m.group() for m in re.finditer(r"[a-z]+|(\d|[.])+|[-+*/%()?:,]|\[|\]", text)]
    for expr in [ atomExpr, funcCallExpr, parenExpr, indexExpr, unaryMinusExpr, binaryStarExpr, binaryMinusExpr, conditionExpr ]:
        seq = expr.parse(seq)
        assert True
        for L in seq_pretty(seq): print L
