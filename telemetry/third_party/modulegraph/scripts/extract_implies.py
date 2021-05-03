#!/usr/bin/env python
"""
This script looks for ImportModules calls in C extensions
of the stdlib.

The current version has harcoded the location of the source
tries on Ronald's machine, a future version will be able
to rebuild the modulegraph source file that contains
this information.
"""

from __future__ import print_function
import re
import os
import sys
import pprint

# The pylint in use is a older version that will consider using io.open() as
# refining builtin functions. This is fixed in a lower version:
#   https://github.com/PyCQA/pylint/issues/464
# For now, we will skip the check for python 3 conversion.
if sys.version_info.major > 2:
    from io import open  # pylint: disable=redefined-builtin

import_re = re.compile('PyImport_ImportModule\w+\("(\w+)"\);')

def extract_implies(root):
    modules_dir = os.path.join(root, "Modules")
    for fn in os.listdir(modules_dir):
        if not fn.endswith('.c'):
            continue

        module_name = fn[:-2]
        if module_name.endswith('module'):
            module_name = module_name[:-6]

        with open(os.path.join(modules_dir, fn)) as fp:
            data = fp.read()

        imports = list(sorted(set(import_re.findall(data))))
        if imports:
            yield module_name, imports



def main():
    for version in ('2.6', '2.7', '3.1'):
        print("====", version)
        pprint.pprint(list(extract_implies('/Users/ronald/Projects/python/release%s-maint'%(version.replace('.', '')))))

if __name__ == "__main__":
    main()
