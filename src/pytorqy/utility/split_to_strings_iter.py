import sys, re

_default_splitting_pattern_arguments = ( r"\d+|[a-zA-Z]+|\r\n|.", re.DOTALL )

if sys.platform == 'cli':
    def split_to_strings_iter(s, pattern=None):
        pattern = pattern or re.compile(*_default_splitting_pattern_arguments)
        for m in pattern.finditer(s):
            b, e = m.span()
            yield s[b:e]
    # if you can ensure the above argument "s" always be just either 
    # str or unicode and never be their derived types, then you need 
    # not use this workaround.
else:
    def split_to_strings_iter(s, pattern=None):
        pattern = pattern or re.compile(*_default_splitting_pattern_arguments)
        for m in pattern.finditer(s):
            yield m.group()