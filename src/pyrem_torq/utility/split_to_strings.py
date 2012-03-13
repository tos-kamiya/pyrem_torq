#coding: utf-8

import re

_default_splitting_pattern_arguments = (r"\d+|[a-zA-Z]+|\r\n|.", re.DOTALL)


def split_to_strings(s, pattern=None):
    r = []; r_append = r.append
    pattern = pattern or re.compile(*_default_splitting_pattern_arguments)
    for m in pattern.finditer(s):
        b, e = m.span()
        r_append(b)
        r_append(s[b:e])
    return r
