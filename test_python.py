# Lint as: python3
"""TODO(rohpavone): DO NOT SUBMIT without one-line documentation for test_python.

TODO(rohpavone): DO NOT SUBMIT without a detailed description of test_python.
"""
import pprint
def SomeFunction(config):
  del config
  return


class SomeClass(object):
  def MyMethod(self, foo=None):
    print('Called my method')

class SomeClassSub(SomeClass):
  def MyMethod(self, foo=None, detail=None):
    print('Called submethod instead')

config = {'ehllo': 'wrold'}
pprint.pprint(config)
SomeFunction(config)
pprint.pprint(config)

SomeClass().MyMethod()
SomeClassSub().MyMethod()

