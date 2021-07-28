# (c) 2005 Ian Bicking and contributors; written for Paste (http://pythonpaste.org)
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
try:
    import pkg_resources
    pkg_resources.declare_namespace(__name__)
except ImportError:
    # don't prevent use of paste if pkg_resources isn't installed
    from pkgutil import extend_path
    __path__ = extend_path(__path__, __name__)
except AttributeError as e:
    import logging
    logging.warning('ATTRIBUTE ERROR: %s' % repr(e))
    import sys
    logging.warning('SYS.PATH: %s' % sys.path)
    logging.warning('SYS.MODULES: %s' % sys.modules)
    import pkg_resources

try:
    import modulefinder
except ImportError:
    pass
else:
    for p in __path__:
        modulefinder.AddPackagePath(__name__, p)
