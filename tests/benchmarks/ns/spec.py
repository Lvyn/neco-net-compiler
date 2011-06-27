import sys, re
sys.path.append('../../../')

from snakes.pnml import loads
from snakes.nets import *

net = loads('model.pnml')

# prog = re.compile(".*(nw|knowledge)$")
# prog2 = re.compile(".*(nonce|peer|spy).*")
# for name, place in net._place.iteritems():
#     if prog.match(name):
#         place.is_OneSafe = False
#     elif prog2.match(name):
#         place.is_OneSafe = True
#     else:
#         #place.is_one_safe = False
#         place.is_OneSafe = True
#         place._check = tBlackToken

if __name__ == '__main__':
    from netcompiler.driver import Driver
    TestRunner()
