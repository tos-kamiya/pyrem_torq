from itertools import islice

def assertion_inpseq_is_empty(inpSeq):
    try: inpSeq.next()
    except StopIteration: pass
    else: assert False

def seq_count_leaf_contents(seq):
    def count_i(item):
        if isinstance(item, list):
            return sum(map(count_i, islice(item, 1, None)))
        return 1
    return count_i(seq)

def seq_visit(seq): # yields ( curPos, in_or_out, node (or item) )
    mark_in, mark_out, mark_item = 1, -1, 0
    def seq_visit_i(curPos, item):
        if not isinstance(item, list):
            yield curPos, mark_item, item
        else:
            assert len(item) >= 1
            yield curPos, mark_in, item
            for i in xrange(1, len(item)):
                for v in seq_visit_i(curPos + [ i ], item[i]):
                    yield v
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

#def seq_outermost_node_iter(seq, label):
#    def soni_i(curPos, item):
#        if _islist(item):
#            assert len(item) >= 1
#            if item[0] == label:
#                yield curPos, item
#            else:
#                for i in xrange(1, len(item)):
#                    for v in soni_i(curPos + [ i ], item[i]):
#                        yield v
#    return soni_i([], seq)

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
            if isinstance(item, list):
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

