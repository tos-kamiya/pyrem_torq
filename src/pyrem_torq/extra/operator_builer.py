from pyrem_torq.expression import *

class OperatorBuilder(object):
    def __init__(self, 
            atomicTermExpr=None, 
            composedTermNodeLabels=None, 
            generatedTermLabel=None):
        self.__ate = atomicTermExpr if atomicTermExpr is not None else Never()
        self.__ctnls = composedTermNodeLabels
        self.__gtl = generatedTermLabel
    
    def set_atomic_term_expr(self, atomicTermExpr):
        assert isinstance(atomicTermExpr, TorqExpression)
        self.__ate = atomicTermExpr
    def get_atomic_term_expr(self):
        return self.__ate
    atomic_term_expr = property(get_atomic_term_expr, set_atomic_term_expr)
    
    def set_composed_term_node_labels(self, labels):
        for lbl in labels: assert lbl # is not empty
        self.__ctnls = frozenset(lbl for lbl in labels)
    def get_composed_term_node_labels(self):
        return sorted(self.__ctnls)
    composed_term_node_labels = property(get_composed_term_node_labels, set_composed_term_node_labels)
    
    def set_generated_term_label(self, label): 
        assert label # is not empty string
        self.__gtl = label
    def get_generated_term_label(self, label): return self.__gtl
    generated_term_label = property(get_generated_term_label, set_generated_term_label)
    
    def _make_term_expr(self, expr0):
        terms = [ self.__ate ]
        terms.extend(NodeMatch(lbl, Search(expr0)) for lbl in self.__ctnls)
        return Or(*terms)
    
    def build_Ot_expr(self, *ops):
        assert self.__ate and self.__ctnls and self.__gtl
        
        signLikeExprs = [] # -123
        castLikeExprs = [] # (int)3.14
        for op in ops:
            if isinstance(op, TorqExpression):
                signLikeExprs.append(op)
            else:
                opOpen, opClose = op
                castLikeExprs.append(( opOpen, opClose ))
        
        opBeginExprs = []
        opBeginExprs.extend(signLikeExprs)
        opBeginExprs.extend(opOpen for opOpen, opClose in castLikeExprs)
            
        expr0 = Holder()
        termExpr = self._make_term_expr(expr0)
        
        ovExprs = []
        for opOpen, opClose in castLikeExprs:
            e = opOpen + [0,None] * (RequireBut(opClose) + (expr0 | Any())) + opClose
            ovExprs.append(e)
        ovExprs.extend(signLikeExprs)
        
        whereShouldNotBeRegardedAsOperator = [0,1] * Or(*opBeginExprs)
        expr = BuildToNode(self.__gtl, [1,None] * Or(*ovExprs) + termExpr) + whereShouldNotBeRegardedAsOperator
        # this "+ [0,1] * Or(*opBeinExprs)" is used to neglect the operator appears after some term.
        
        expr0.expr = expr | (termExpr + whereShouldNotBeRegardedAsOperator)
        return Search(expr0)
    
    def build_tO_expr(self, *ops):
        assert self.__ate and self.__ctnls and self.__gtl
        
        repeatLikeExprs = [] # \d+
        callLikeExprs = [] # f(1, 2)
        for op in ops:
            if isinstance(op, TorqExpression):
                repeatLikeExprs.append(op)
            else:
                opOpen, opClose = op
                callLikeExprs.append(( opOpen, opClose ))
        
        expr0 = Holder()
        termExpr = self._make_term_expr(expr0)
        
        terms = [ self.__ate ]
        terms.extend(Node(lbl) for lbl in self.__ctnls)
        whereTermShouldNotAppear = RequireBut(Or(*terms))
        
        voExprs = []
        for opOpen, opClose in callLikeExprs:
            e = opOpen + [0,None] * (RequireBut(opClose) + (expr0 | Any())) + opClose + whereTermShouldNotAppear
            voExprs.append(e)
        for op in repeatLikeExprs:
            e = op + whereTermShouldNotAppear
            voExprs.append(e)
        
        expr = BuildToNode(self.__gtl, termExpr + [1,None] * Or(*voExprs))
        expr0.expr = expr | termExpr
        return Search(expr0)
    
    def build_tOt_expr(self, *ops):
        assert self.__ate and self.__ctnls and self.__gtl
        
        addLikeExprs = [] # 1 + 2
        conditionLikeExprs = [] # flag ? 1 : 0
        
        for op in ops:
            if isinstance(op, TorqExpression):
                addLikeExprs.append(op)
            else:
                opOpen, opClose = op
                conditionLikeExprs.append(( opOpen, opClose ))
        
        expr0 = Holder()
        termExpr = self._make_term_expr(expr0)
        
        vowExprs = []
        for opOpen, opClose in conditionLikeExprs:
            e = opOpen + [0,None] * (RequireBut(opClose) + (expr0 | Any())) + opClose
            vowExprs.append(e)
        vowExprs.extend(addLikeExprs)
        
        expr = BuildToNode(self.__gtl, termExpr + [1,None] * (Or(*vowExprs) + termExpr))
        expr0.expr = expr | termExpr
        return Search(expr0)
    
    def build_O_expr(self, *ops):
        assert self.__ate and self.__ctnls and self.__gtl
        
        expr0 = Holder()
        termExpr = self._make_term_expr(expr0)
        
        ovpExprs = []
        for opOpen, opClose in ops:
            e = BuildToNode(self.__gtl, opOpen + [0,None] * (RequireBut(opClose) + (expr0 | Any())) + opClose)
            ovpExprs.append(e)
        ovpExprs.append(termExpr)
        expr = Or(*ovpExprs)
        expr0.expr = expr | termExpr
        return Search(expr0)

if __name__ == '__main__':
    import re
    from pyrem_torq.treeseq import seq_pretty
    
    kit = OperatorBuilder()
    kit.atomic_term_expr = Rex(r"^\d") | Rex(r"^\w")
    kit.composed_term_node_labels = ( "t", )
    kit.generated_term_label = "t"
    
    descAndExprs = []
    descAndExprs.append(( "funcCallExpr", kit.build_tO_expr(( Literal("("), Literal(")") )) ))
    descAndExprs.append(( "parenExpr", kit.build_O_expr(( Literal("("), Literal(")") )) ))
    descAndExprs.append(( "indexExpr", kit.build_tO_expr(( Literal("["), Literal("]") )) ))
    descAndExprs.append(( "unaryMinusExpr", kit.build_Ot_expr(Literal("-")) ))
    descAndExprs.append(( "binaryStarExpr", kit.build_tOt_expr(Literal("*")) ))
    descAndExprs.append(( "binaryMinusExpr", kit.build_tOt_expr(Literal("-")) ))
    descAndExprs.append(( "conditionExpr", kit.build_tOt_expr(( Literal("?"), Literal(":") )) ))
    
    text = "-1-2*(3-4)-a[5]*6?7:8-9?b(c,d):e"
    seq = [ 'code' ] + [m.group() for m in re.finditer(r"[a-z]+|(\d|[.])+|[-+*/%()?:,]|\[|\]", text)]
    for desc, expr in descAndExprs:
        print "step: %s" % desc
        seq = expr.parse(seq)
        assert True
        for L in seq_pretty(seq): print L
