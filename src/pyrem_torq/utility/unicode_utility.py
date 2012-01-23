#coding: utf-8

if hasattr("123", "__int__") or hasattr(u"123", "__int__"):
    raise ImportError, "module pyrem_torq.utility assumes str type doesn't have a method __int__()"

class SurrogatePairCollapsed(ValueError):
    pass

def to_codepoint_list(s):
    assert isinstance(s, unicode)
    r = []; r_append = r.append
    upper = None
    for c in s:
        code = ord(c)
        if not(0xd800 <= code <= 0xdfff):
            r_append(code)
        else:
            if code <= 0xdbff:
                if upper is None: raise SurrogatePairCollapsed
                r_append(0x10000 + (((upper & 0x3ff) << 10) | (code & 0x3ff)))
                upper = None
            else:
                if upper is not None: raise SurrogatePairCollapsed 
                upper = code
    if upper is not None: raise SurrogatePairCollapsed
    return r

try:
    __temp = unichr(0x26951)
    # the python interpreter doesn't use a surrogate pair

    def to_unicode_string(L):
        return u''.join(map(unicode, L))
    
    def split_to_ucs4char(s):
        assert isinstance(s, unicode)
        return list(s)
except:
    def to_unicode_string(L):
        r = []
        r_append = r.append
        for c in L:
            try:
                c = c.__int__()
                if c < 0x10000:
                    r_append(c)
                else:
                    value = c - 0x10000
                    upper, lower = 0xd800 | (value >> 10), 0xdc00 | (c & 0x3ff)
                    assert 0xd800 <= upper <= 0xdbff
                    assert 0xdc00 <= lower <= 0xdfff
                    r_append(upper)
                    r_append(lower)
            except:
                r_append(c)
        return u''.join(map(unicode, r))

    def split_to_ucs4char(s):
        assert isinstance(s, unicode)
        r = []; r_append = r.append
        for c in s:
            if u'\udc00' <= c <= u'\udfff': # lower of a surrogate pair
                assert u'\ud800' <= r[-1] <= u'\udbff' # upper of a surrogate pair
                r[-1] += c
            else:
                r_append(c)
        return r

if __name__ == '__main__':
    s = u"abc" + u"\u3042\u3044\u3046" + u"\uD840\uDC0B"
    cp = to_codepoint_list(s)
    print cp
    us = to_unicode_string(s)
    print repr(us)
    sc = split_to_ucs4char(s)
    print repr(sc)
