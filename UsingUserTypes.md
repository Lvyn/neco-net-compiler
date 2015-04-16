# Using User defined objects #

## Python backend ##

To use user _defined objects_ as tokens in a Petri net, the user need to provide:
  * a hash function: `__hash__`
  * comparison functions: `__eq__` and `__ne__`

## Cython backend ##

To use user _defined objects_ as tokens in a Petri net, the user need to provide:
  * a hash function: `__hash__`
  * comparison functions: `__lt__`, `__gt__`, `__eq__` and `__ne__`

## Example of user defined type ##

This class is usable from Python and Cython.
```
class UserDefined(object):
    def __init__(self, s):
        self.data = s

    def transform(self):
        tmp = UserDefined(self.data.upper())
        return tmp

    def __eq__(self, other):
        return self.data == other.data

    def __ne__(self, other):
        return self.data != other.data

    def __hash__(self):
        return hash(self.data)

    def __lt__(self, other):
        return self.data < other.data

    def __gt__(self, other):
        return self.data > other.data

    def __repr__(self):
        return 'UserDefined({!r})'.format(self.data)
```