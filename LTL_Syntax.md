# LTL formula syntax #

  1. Unary prefix operators
    * `not` : not.
    * `F` : eventually.
    * `G` : always (a.k.a. henceforth, from now on, ...).
    * `X` : next.
  1. Binary operators
    * `and` : and.
    * `or` : or.
    * `=>`, `->`: implies.
    * `<=>`, `<->`: equivalence.
    * `xor` : xor.
    * `U` : until.
  1. Atomic propositions
    1. boolean expressions:
      * `multiset1 CMP multiset2` : multiset comparison where CMP is in { `<=`, `<`, `>=`, `>`, `=`, `!=` }
      * `int_expr CMP int_expr` : integer expression comparisons where CMP is in { `<=`, `<`, `>=`, `>`, `=`, `!=` }
      * `fireable(trans)` : true if transition `trans` is fireable
      * `deadlock` : true if current state is a deadlock, ie., there is no fireable transition.
    1. multiset expressions
      * `marking(id)` : marking of place 'id'
      * `[ token1, token2, ... ]` : multiset represented as a list, where `token_i` are token values. Accepted values are: `dot` (blacktoken), integers (`1`, `2`, ...), string identifiers (`"meow"`).
      * `$ python code $` : this multiset expression allows to use arbitrary python code, however it is closery related to implementation. The return value of the code should have type `ctypes_ext.Multiset`. Please refer to file `neco/ctypes/ctypes_ext.pyx` for more details.
    1. integer expressions
      * integers : `1`, `2`, ...
      * `card( multiset )` : number of tokens in a multiset (usually a marking), for example `card(marking(place1))`.
      * `int_expr + int_expr` : sums of integer expressions

# Some examples #
```
F (marking(my_place) = [1, 2, 3])
```

```
G (card(marking(place1)) + card(marking(place2)) <= 1)
```

```
G (marking(place1) = [] <=> marking(place2) = [dot])
```

```
G (marking(place1) = [] => marking(place2) != [])
```

```
G (marking(place1) != [] => (fireable(trans1) and card(marking(place1)) = 1))
```

# Advanced example with Python expressions #

Let us consider the following model:

```
from snakes.nets import *

# user defined token type
class UserDefined(object):
    def __init__(self, string):
        self.data = string

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

net = PetriNet('Net')
net.processes = []
net.globals['UserDefined'] = UserDefined

s1 = Place('s1', [UserDefined('test')])
s2 = Place('s2', [])

net.add_place(s1)
net.add_place(s2)

transition = Transition('t', Expression('True'))
net.add_transition(transition)

net.add_input('s1', 't', Variable('x'))
net.add_output('s2', 't', Expression('x.transform()'))
```

First, we compile this model
```
neco-compile -lcython -m model.py
```

Then, we build the checker module
```
neco-check --formula="F (marking(s2) = $ ctypes_ext.MultiSet({ net.UserDefined('TEST') : 1 }) $)"
```

Finally we run the checking algorithm
```
neco-spot neco_formula
```

More complicated formulas can be checked like:
```
G ((marking(s1) = $ ctypes_ext.MultiSet({ net.UserDefined('test') : 1 }) $) => X (marking(s2) = $ ctypes_ext.MultiSet({ net.UserDefined('TEST') : 1 }) $))
```
or
```
G (((marking(s1) = $ ctypes_ext.MultiSet({ net.UserDefined('test') : 1 }) $) => X (marking(s2) = $ ctypes_ext.MultiSet({ net.UserDefined('TEST') : 1 }) $)) and card(marking(s1)) + card(marking(s2)) = 1)
```