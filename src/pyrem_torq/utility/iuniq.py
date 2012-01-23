#coding: utf-8

import itertools

def iuniq(enu):
    ps, qs = itertools.tee(enu, 2)
    yield ps.next()
    for p, q in itertools.izip(ps, qs):
        if p != q:
            yield p
