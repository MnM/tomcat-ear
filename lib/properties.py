def p_empty_or_comment(line, comment='#'):
    """Predicate matching strings that are not empty and don't start
    with a comment character. For best results, the line should no
    longer contain whitespace at the start."""
    return len(line) and not line.startswith(comment)

def mreplace(s, replacements=[]):
    """Apply multiple replace operations to the string s. The
    replacements are a list of (old, new) tuples."""
    return reduce(lambda x, rep: apply(x.replace, rep), replacements, s)

def split_and_replace(s, split=',', replace={}):
    # variable replacements use the format ${var}. Here, we build
    # tuples out of the replace dict that can be applied to the
    # str.replace function:
    replacements = [("${%s}" % key, value)
                    for key, value in replace.iteritems()]
    list = [mreplace(item, replacements) for item in s.split(split)]
    return list[0] if len(list) is 1 else list

def resolve_continuation(l, char='\\'):
    """Concatenates elements of the given string list with the
    following one, if they end with the continuation character."""
    result = []
    temp = ''
    for line in l:
        if not line.endswith(char):
            result.append(temp + line if len(temp) else line)
            temp = ''
        else:
            temp += line.rstrip(" \t\\")
    
    if len(temp):
        raise EOFError(temp)
    return result

def parse_properties(fhandle, replace={}, assign='=', comment='#', split=','):
    """Reads a .properties file and returns it's contents as a
    dict. If the values of this dict contain the split character, a
    str.split operation on this character is automatically applied,
    resulting in a list of strings. Otherwise, values are
    strings. Optionally, a dictionary of replacements can be given to
    automatically expand variables. This expansion is applied last
    (i. e. after the comment/assign/split parsing), so that variables
    cannot 'inject' syntax elements.

    The kwargs 'assign' and 'comment' can be used, if your .properties
    file uses a different syntax."""
    if type(fhandle) != file:
        raise ValueError("file expected")

    # read all lines, strip them, ignore comments and resolve
    # continuations (lines ending with '\')
    lines = resolve_continuation(
        filter(lambda x: p_empty_or_comment(x, comment),
               [line.strip() for line in fhandle]))

    # split on the first assignment character, build a list of tuples
    kv_tuples = [tuple(l.split(assign, 1)) for l in lines]

    # strip key and value again and apply replacements
    return dict([(key.strip(), split_and_replace(value.strip(), split, replace))
                 for (key, value) in kv_tuples])
