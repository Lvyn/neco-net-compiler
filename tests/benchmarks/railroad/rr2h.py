import sys
from  snakes.nets import *

net = loads(sys.argv[1])

node = {}

for i, place in enumerate(net.place()) :
    node[place.name] = "p%s" % i
for i, trans in enumerate(net.transition()) :
    node[trans.name] = "t%s" % i

print "%s {" % sys.argv[1].split(".")[0].replace("-", "")

print "    type dot : enum (DOT);"
print

for place in net.place() :
    name = node[place.name]
    if ".entry" in place.name :
        dom = "dot"
    elif ".exit" in place.name :
        dom = "dot"
    elif ".internal" in place.name :
        dom = "dot"
    elif place._check == tBlackToken :
        dom = "dot"
    else :
        dom = "int"
    init = " + ".join("<( %s )>" % t for t in place.tokens).upper()
    print "    // %s" % place.name
    if place.tokens :
        print "    place %s {dom: %s; init: %s;}" % (name, dom, init)
    else :
        print "    place %s {dom: %s;}" % (name, dom)

print

def arc2str (arc, todo=None) :
    if isinstance(arc, Value) :
        return str(arc).upper()
    elif isinstance(arc, Variable):
        if str(arc) == 'dot':
            return 'DOT'
        return str(arc)
    elif isinstance(arc, Test) :
        if todo is not None :
            todo.append(arc._annotation)
        return arc2str(arc._annotation)
    elif isinstance(arc, Expression) :
        return str(arc)
    assert False, "unsupported arc: %r" % arc

for trans in net.transition() :
    out = {}
    name = node[trans.name]
    print "    // %s" % trans.name
    print "    transition %s {" % name
    print "        in {"
    for place, arc in trans.input() :
        todo = []
        src = node[place.name]
        print "            // %s" % place.name
        print "            %s: <( %s )>;" % (src, arc2str(arc, todo))
        if todo :
            out[place] = todo
    print "        }"
    print "        out {"
    for place, cons in out.items() :
        src = node[place.name]
        for arc in cons :
            print "            // %s" % place.name
            print "            %s: <( %s )>;" % (src, arc2str(arc))
    for place, arc in trans.output() :
        src = node[place.name]
        print "            // %s" % place.name
        print "            %s: <( %s )>;" % (src, arc2str(arc))
    print "        }"
    if trans.guard != Expression("True") :
        print "    guard: %s;" % str(trans.guard).replace("==", "=")
    print "    }"
    print

print "}"
