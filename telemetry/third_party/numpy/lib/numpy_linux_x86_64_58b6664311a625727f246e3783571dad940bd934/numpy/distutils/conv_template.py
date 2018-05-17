#!/usr/bin/python
"""
takes templated file .xxx.src and produces .xxx file  where .xxx is
.i or .c or .h, using the following template rules

/**begin repeat  -- on a line by itself marks the start of a repeated code
                    segment
/**end repeat**/ -- on a line by itself marks it's end

After the /**begin repeat and before the */, all the named templates are placed
these should all have the same number of replacements

Repeat blocks can be nested, with each nested block labeled with its depth,
i.e.
/**begin repeat1
 *....
 */
/**end repeat1**/

When using nested loops, you can optionally exlude particular
combinations of the variables using (inside the comment portion of the inner loop):

 :exclude: var1=value1, var2=value2, ...

This will exlude the pattern where var1 is value1 and var2 is value2 when
the result is being generated.


In the main body each replace will use one entry from the list of named replacements

 Note that all #..# forms in a block must have the same number of
   comma-separated entries.

Example:

    An input file containing

        /**begin repeat
         * #a = 1,2,3#
         * #b = 1,2,3#
         */

        /**begin repeat1
         * #c = ted, jim#
         */
        @a@, @b@, @c@
        /**end repeat1**/

        /**end repeat**/

    produces

        line 1 "template.c.src"

        /*
         *********************************************************************
         **       This file was autogenerated from a template  DO NOT EDIT!!**
         **       Changes should be made to the original source (.src) file **
         *********************************************************************
         */

        #line 9
        1, 1, ted

        #line 9
        1, 1, jim

        #line 9
        2, 2, ted

        #line 9
        2, 2, jim

        #line 9
        3, 3, ted

        #line 9
        3, 3, jim

"""
from __future__ import division, absolute_import, print_function


__all__ = ['process_str', 'process_file']

import os
import sys
import re

from numpy.distutils.compat import get_exception

# names for replacement that are already global.
global_names = {}

# header placed at the front of head processed file
header =\
"""
/*
 *****************************************************************************
 **       This file was autogenerated from a template  DO NOT EDIT!!!!      **
 **       Changes should be made to the original source (.src) file         **
 *****************************************************************************
 */

"""
# Parse string for repeat loops
def parse_structure(astr, level):
    """
    The returned line number is from the beginning of the string, starting
    at zero. Returns an empty list if no loops found.

    """
    if level == 0 :
        loopbeg = "/**begin repeat"
        loopend = "/**end repeat**/"
    else :
        loopbeg = "/**begin repeat%d" % level
        loopend = "/**end repeat%d**/" % level

    ind = 0
    line = 0
    spanlist = []
    while True:
        start = astr.find(loopbeg, ind)
        if start == -1:
            break
        start2 = astr.find("*/", start)
        start2 = astr.find("\n", start2)
        fini1 = astr.find(loopend, start2)
        fini2 = astr.find("\n", fini1)
        line += astr.count("\n", ind, start2+1)
        spanlist.append((start, start2+1, fini1, fini2+1, line))
        line += astr.count("\n", start2+1, fini2)
        ind = fini2
    spanlist.sort()
    return spanlist


def paren_repl(obj):
    torep = obj.group(1)
    numrep = obj.group(2)
    return ','.join([torep]*int(numrep))

parenrep = re.compile(r"[(]([^)]*)[)]\*(\d+)")
plainrep = re.compile(r"([^*]+)\*(\d+)")
def parse_values(astr):
    # replaces all occurrences of '(a,b,c)*4' in astr
    # with 'a,b,c,a,b,c,a,b,c,a,b,c'. Empty braces generate
    # empty values, i.e., ()*4 yields ',,,'. The result is
    # split at ',' and a list of values returned.
    astr = parenrep.sub(paren_repl, astr)
    # replaces occurences of xxx*3 with xxx, xxx, xxx
    astr = ','.join([plainrep.sub(paren_repl, x.strip())
                     for x in astr.split(',')])
    return astr.split(',')


stripast = re.compile(r"\n\s*\*?")
named_re = re.compile(r"#\s*(\w*)\s*=([^#]*)#")
exclude_vars_re = re.compile(r"(\w*)=(\w*)")
exclude_re = re.compile(":exclude:")
def parse_loop_header(loophead) :
    """Find all named replacements in the header

    Returns a list of dictionaries, one for each loop iteration,
    where each key is a name to be substituted and the corresponding
    value is the replacement string.

    Also return a list of exclusions.  The exclusions are dictionaries
     of key value pairs. There can be more than one exclusion.
     [{'var1':'value1', 'var2', 'value2'[,...]}, ...]

    """
    # Strip out '\n' and leading '*', if any, in continuation lines.
    # This should not effect code previous to this change as
    # continuation lines were not allowed.
    loophead = stripast.sub("", loophead)
    # parse out the names and lists of values
    names = []
    reps = named_re.findall(loophead)
    nsub = None
    for rep in reps:
        name = rep[0]
        vals = parse_values(rep[1])
        size = len(vals)
        if nsub is None :
            nsub = size
        elif nsub != size :
            msg = "Mismatch in number of values:\n%s = %s" % (name, vals)
            raise ValueError(msg)
        names.append((name, vals))


    # Find any exclude variables
    excludes = []

    for obj in exclude_re.finditer(loophead):
        span = obj.span()
        # find next newline
        endline = loophead.find('\n', span[1])
        substr = loophead[span[1]:endline]
        ex_names = exclude_vars_re.findall(substr)
        excludes.append(dict(ex_names))

    # generate list of dictionaries, one for each template iteration
    dlist = []
    if nsub is None :
        raise ValueError("No substitution variables found")
    for i in range(nsub) :
        tmp = {}
        for name, vals in names :
            tmp[name] = vals[i]
        dlist.append(tmp)
    return dlist

replace_re = re.compile(r"@([\w]+)@")
def parse_string(astr, env, level, line) :
    lineno = "#line %d\n" % line

    # local function for string replacement, uses env
    def replace(match):
        name = match.group(1)
        try :
            val = env[name]
        except KeyError:
            msg = 'line %d: no definition of key "%s"'%(line, name)
            raise ValueError(msg)
        return val

    code = [lineno]
    struct = parse_structure(astr, level)
    if struct :
        # recurse over inner loops
        oldend = 0
        newlevel = level + 1
        for sub in struct:
            pref = astr[oldend:sub[0]]
            head = astr[sub[0]:sub[1]]
            text = astr[sub[1]:sub[2]]
            oldend = sub[3]
            newline = line + sub[4]
            code.append(replace_re.sub(replace, pref))
            try :
                envlist = parse_loop_header(head)
            except ValueError:
                e = get_exception()
                msg = "line %d: %s" % (newline, e)
                raise ValueError(msg)
            for newenv in envlist :
                newenv.update(env)
                newcode = parse_string(text, newenv, newlevel, newline)
                code.extend(newcode)
        suff = astr[oldend:]
        code.append(replace_re.sub(replace, suff))
    else :
        # replace keys
        code.append(replace_re.sub(replace, astr))
    code.append('\n')
    return ''.join(code)

def process_str(astr):
    code = [header]
    code.extend(parse_string(astr, global_names, 0, 1))
    return ''.join(code)


include_src_re = re.compile(r"(\n|\A)#include\s*['\"]"
                            r"(?P<name>[\w\d./\\]+[.]src)['\"]", re.I)

def resolve_includes(source):
    d = os.path.dirname(source)
    fid = open(source)
    lines = []
    for line in fid:
        m = include_src_re.match(line)
        if m:
            fn = m.group('name')
            if not os.path.isabs(fn):
                fn = os.path.join(d, fn)
            if os.path.isfile(fn):
                print('Including file', fn)
                lines.extend(resolve_includes(fn))
            else:
                lines.append(line)
        else:
            lines.append(line)
    fid.close()
    return lines

def process_file(source):
    lines = resolve_includes(source)
    sourcefile = os.path.normcase(source).replace("\\", "\\\\")
    try:
        code = process_str(''.join(lines))
    except ValueError:
        e = get_exception()
        raise ValueError('In "%s" loop at %s' % (sourcefile, e))
    return '#line 1 "%s"\n%s' % (sourcefile, code)


def unique_key(adict):
    # this obtains a unique key given a dictionary
    # currently it works by appending together n of the letters of the
    #   current keys and increasing n until a unique key is found
    # -- not particularly quick
    allkeys = list(adict.keys())
    done = False
    n = 1
    while not done:
        newkey = "".join([x[:n] for x in allkeys])
        if newkey in allkeys:
            n += 1
        else:
            done = True
    return newkey


if __name__ == "__main__":

    try:
        file = sys.argv[1]
    except IndexError:
        fid = sys.stdin
        outfile = sys.stdout
    else:
        fid = open(file, 'r')
        (base, ext) = os.path.splitext(file)
        newname = base
        outfile = open(newname, 'w')

    allstr = fid.read()
    try:
        writestr = process_str(allstr)
    except ValueError:
        e = get_exception()
        raise ValueError("In %s loop at %s" % (file, e))
    outfile.write(writestr)
