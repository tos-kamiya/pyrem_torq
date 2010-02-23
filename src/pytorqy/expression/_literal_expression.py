import re

from pytorqy.utility import SingletonWoInitArgs
from ._expression import TorqExpression

class Literal(TorqExpression):
    __slots__ = [ '__string' ]
    
    def __init__(self, s):
        self.__string = s
    
    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        if self.__string == lookAheadString:
            return 1, ( lookAheadString, ), ()
        #return None
    
    def __eq__(self, right): return isinstance(right, Literal) and self.__string == right.__string
    def __repr__(self): return "Literal(%s)" % repr(self.__string)
    def __hash__(self): return hash("Literal") + hash(self.__string)
    
    def extractStrings(self):
        return [ self.__string ]
    
    def required_node_literal_epsilon(self):
        return (), ( self.__string, ), False
            
    @staticmethod
    def build(s): return Literal(s)

    def or_merged(self, other):
        if isinstance(other, AnyLiteral):
            return other
        if isinstance(other, ( Literal, LiteralClass )):
            return LiteralClass.merged([ self, other ])
        return None

class AnyLiteral(TorqExpression): # singleton
    __metaclass__ = SingletonWoInitArgs
    __slots__ = [ ]
    
    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        return 1, ( lookAheadString, ), ()
    
    def __eq__(self, right): return isinstance(right, AnyLiteral)
    def __repr__(self): return "AnyLiteral()"
    def __hash__(self): return hash("AnyLiteral")
    
    @staticmethod
    def build(): return AnyLiteral()

    def or_merged(self, other):
        if isinstance(other, ( Literal, LiteralClass, AnyLiteral )):
            return self
        return None

class LiteralClass(TorqExpression):
    __slots__ = [ '__strings', '__stringSet' ]
    
    def __init__(self, strings):
        assert len(strings) > 0
        self.__strings = tuple(sorted(strings))
        self.__stringSet = frozenset(self.__strings)
    
    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        if lookAheadString in self.__stringSet: 
            return 1, ( lookAheadString, ), ()
        #return None
    
    def __eq__(self, right): return isinstance(right, LiteralClass) and self.__strings == right.__strings
    def __repr__(self): return "LiteralClass(%s)" % (",".join(repr(s) for s in self.__strings))
    def __hash__(self): return hash("LiteralClass") + sum(map(hash, self.__strings))
    
    def extractStrings(self):
        return sorted(self.__strings)
    
    def required_node_literal_epsilon(self):
        return (), self.__strings, False
            
    def or_merged(self, other):
        if isinstance(other, AnyLiteral):
            return other
        if isinstance(other, ( Literal, LiteralClass )):
            return LiteralClass.merged([ self, other ])
        return None
    
    @staticmethod
    def merged(literalExprOrliteralClassExprs):
        mergedStrings = []
        for item in literalExprOrliteralClassExprs:
            assert isinstance(item, ( Literal, LiteralClass ))
            mergedStrings.extend(item.extractStrings())
        return LiteralClass(mergedStrings)

    @staticmethod
    def build(strings): return LiteralClass(strings)

class RexCompilationUnable(ValueError):
    pass

class Rex(TorqExpression):
    __slots__ = [ '__expression_match', '__expressionstr', '__ignoreCase' ]
    
    def __init__(self, exprStr, ignoreCase=False):
        try:
            flags = re.DOTALL
            if ignoreCase: flags |= re.IGNORECASE
            pat = re.compile(exprStr, flags)
        except Exception as e:
            raise RexCompilationUnable("invalid regex string: %s" % repr(exprStr))
        self.__expression_match = pat.match
        self.__expressionstr = exprStr
        self.__ignoreCase = ignoreCase
        
    def _match_lit(self, inpSeq, inpPos, lookAheadString):
        if self.__expression_match(lookAheadString):
            return 1, ( lookAheadString, ), ()
        #return None
    
    def __eq__(self, right): return isinstance(right, Rex) and \
        self.__expressionstr == right.__expressionstr and self.__ignoreCase == right.__ignoreCase
    
    def __repr__(self): return "Rex(%s,ignoreCase=%s)" % ( repr(self.__expressionstr), repr(self.__ignoreCase) ) 
    def __hash__(self): return hash("Rex") + hash(self.__expressionstr)
    
    @staticmethod
    def build(exprStr, ignoreCase=False): return Rex(exprStr, ignoreCase)
