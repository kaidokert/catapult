#
# This file is part of pyasn1 software.
#
# Copyright (c) 2005-2017, Ilya Etingof <etingof@gmail.com>
# License: http://pyasn1.sf.net/license.html
#
from sys import version_info

if version_info[:2] <= (2, 5):

    def partition(string, sep):
        try:
            a, c = string.split(sep, 1)

        except ValueError:
            a, b, c = string, '', ''

        else:
            b = sep

        return a, b, c

else:

    def partition(string, sep):
        return string.partition(sep)
