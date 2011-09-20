from itertools import islice
from collections import deque

def assertion_inpseq_is_empty(inpSeq):
    try: inpSeq.next()
    except StopIteration: pass
    else: assert False

def seq_count_leaf_contents(seq):
    def count_i(item):
        if item.__class__ is list:
            return sum(map(count_i, islice(item, 1, None)))
        return 1
    return count_i(seq)

def seq_visit(seq): # yields ( curPos, in_or_out, node (or item) )
    mark_in, mark_out, mark_item = 1, -1, 0
    def seq_visit_i(curPos, item):
        if item.__class__ is not list:
            yield curPos, mark_item, item
        else:
            assert len(item) >= 1
            yield curPos, mark_in, item
            for i in xrange(1, len(item)):
                for v in seq_visit_i(curPos + [ i ], item[i]): yield v # need PEP380
            yield curPos, mark_out, item
    return seq_visit_i([], seq)

def seq_walk(seq): # yields ( curPos, nodeName, node (or item) )
    for curPos, in_or_out, node_or_item in seq_visit(seq):
        if in_or_out == 1:
            # get in to a node
            yield curPos, node_or_item[0], node_or_item
        elif in_or_out == 0:
            yield curPos, None, node_or_item
        else:
            # get out from a node
            pass

def seq_outermost_node_iter(seq, label):
    def soni_i(curPos, item):
        if item.__class__ is not list:
            assert len(item) >= 1
            if item[0] == label:
                yield curPos, item
            else:
                for i in xrange(1, len(item)):
                    for v in soni_i(curPos + [ i ], item[i]): yield v # need PEP380
    return soni_i([], seq)

def seq_pretty(seq):
    def find_type_range(type, seq, beginPos):
        assert beginPos >= 1
        len_seq = len(seq)
        if not(beginPos < len_seq and isinstance(seq[beginPos], type)):
            return None
        for i in xrange(beginPos + 1, len_seq):
            if not isinstance(seq[i], type): return i
        return len_seq
    r = []
    def seq_pretty_i(seq, indent):
        if len(seq) == 1:
            r.append(indent + "[ %s: ]" % ( seq[0] ))
            return
        len_seq = len(seq)
        if find_type_range(str, seq, 1) == len_seq:
            r.append(indent + "[ %s: %s ]" % ( seq[0], ",".join(map(repr, islice(seq, 1, None)))))
            return
        if find_type_range(unicode, seq, 1) == len_seq:
            r.append(indent + "[ %s: %s ]" % ( seq[0], u",".join(map(repr, islice(seq, 1, None)))))
            return
        
        newIndent = indent + "  "
        r.append(indent + "[ %s:" % seq[0])
        i = 1
        while i < len_seq:
            item = seq[i]
            if item.__class__ is list:
                seq_pretty_i(item, newIndent)
                i += 1
                continue # while i
            endPos = find_type_range(str, seq, i)
            if endPos:
                r.append(newIndent + ",".join(map(repr, seq[i:endPos])))
                i = endPos
                continue # while i
            endPos = find_type_range(unicode, seq, i)
            if endPos:
                r.append(newIndent + ",".join(map(repr, seq[i:endPos])))
                i = endPos
                continue # while i
            r.append(newIndent + repr(item))
            i += 1
        r.append(indent + "]")
    seq_pretty_i(seq, "")
    return r

def seq_split_nodes_of_label(seq, label):
    removedItems = []; removedItems_append = removedItems.append
    def _seq_split_nodes_of_label_i(seq):
        r = []; r_append = r.append
        q = iter(seq)
        r_append(q.next())
        for item in q:
            if item.__class__ is list:
                if item[0] == label:
                    removedItems_append(item)
                else:
                    r_append(_seq_split_nodes_of_label_i(item))
            else:
                r_append(item)
                r_append(q.next())
        return r
    r = _seq_split_nodes_of_label_i(seq)
    return r, removedItems

def seq_remove_strattrs(seq):
    r = []; r_append = r.append
    q = deque(seq); q_pl = q.popleft
    r_append(q_pl())
    while q:
        item = q_pl()
        if item.__class__ is list:
            r_append(seq_remove_strattrs(item))
        else:
            r_append(q_pl())
    return r
            
def seq_extract_strattrs(seq):
    r = []; r_append = r.append
    q = deque(seq); q_pl = q.popleft
    r_append(q_pl())
    while q:
        item = q_pl()
        if item.__class__ is list:
            r_append(seq_extract_strattrs(item))
        else:
            r_append(item)
            q_pl()
    return r
            
def seq_split_strattrs(seq):
    a = []; a_append = a.append
    s = []; s_append = s.append
    q = deque(seq); q_pl = q.popleft
    item = q_pl()
    a_append(item)
    s_append(item)
    while q:
        item = q_pl()
        if item.__class__ is list:
            ai, si = seq_split_strattrs(item)
            a_append(ai)
            s_append(si)
        else:
            a_append(item)
            s_append(q_pl())
    return a, s
            
def seq_merge_strattrs(atrSeq, strSeq):
    assert len(atrSeq) == len(strSeq)
    assert strSeq[0] == atrSeq[0]
    r = [ strSeq[0] ]; r_append = r.append
    for aItem, sItem in zip(atrSeq[1:], strSeq[1:]):
        if aItem.__class__ is list:
            r_append(seq_merge_strattrs(aItem, sItem))
        else:
            r_append(aItem)
            r_append(sItem)
    return r
            
def seq_enclose_strattrs(seq):
    r = []; r_append = r.append
    q = deque(seq); q_pl = q.popleft
    r_append(q_pl())
    while q:
        item = q_pl()
        if item.__class__ is list:
            r_append(seq_enclose_strattrs(item))
        else:
            r_append(( item, q_pl() ))
    return r

def seq_disclose_strattrs(seq):
    r = []; r_append = r.append; r_extend = r.extend
    q = deque(seq); q_pl = q.popleft
    r_append(q_pl())
    while q:
        item = q_pl()
        if item.__class__ is list:
            r_append(seq_disclose_strattrs(item))
        elif item.__class__ is tuple:
            assert len(item) == 2
            r_extend(item)
        else:
            raise TypeError("wrong type item: %s" % repr(item))
    return r
    