#import expression_shortname
import operator_builer

# other stuff

class NodeWithOrigin(list):
    __slots__ = [ 'original' ]
    
    def __init__(self, content, original):
        list.__init__(self, content)
        self.original = original
        
    def __repr__(self): return "NodeWithOrigin(%s,%s)" % (list.__repr__(self), repr(self.original))
