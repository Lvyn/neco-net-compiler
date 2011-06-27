import sys
import snakes.plugins
snakes.plugins.load("gv", "snakes.nets", "snk")

def trans (trans, mode, attr) :
    if "this=" in trans.name :
        name = trans.name.replace("this=", "")
        num = name.split("(")[1].split(")")[0]
    else :
        name = trans.name
        num = None
    if "down-(dot)" in name :
        label = "g.down"
    elif "state+(0)" in name :
        label = "g.close"
    elif "state+(2)" in name :
        label = "g.open"
    elif "up-(dot)" in name :
        label = "g.up"
    elif "enter+(dot)" in name :
        label = "t%s.enter" % num
    elif "crossing+(dot)" in name :
        label = "t%s.cross" % num
    elif "crossing-(dot)" in name :
        label = "t%s.leave" % num
    elif "if (c) == (0)" in name :
        label = "c.first"
    elif "if (c) > (0)" in name :
        label = "c.enter"
    elif "if (c) == (1)" in name :
        label = "c.last"
    elif "if (c) > (1)" in name :
        label = "c.leave"
    elif "done-(0)" in name :
        label = "c.close"
    elif "done-(2)" in name :
        label = "c.open"
    else :
        label = name
    attr["label"] = label

def state (num, graph, attr) :
    gate = {2: "open", 1: "moving", 0:"closed"}
    track = []
    m = graph.net.get_marking()
    for p in m :
        if p.startswith("track") and p.endswith(".crossing") :
            track.append(p.split("=")[1].split(")")[0])
    label = "%s/%s/%s" % (gate[list(m("gate().state"))[0]],
                          list(m("controller().count"))[0],
                          ",".join(sorted(track)) if track else "none")
    green = "%s/%s" % ("+" if m("green_all") else "-",
                       ",".join(str(x) for x in m("green_one")))
    attr["label"] = "%s\\n%s\\n%s" % (num, label, green)

def printstate (m) :
    for p in m :
        print "#", p, "=", m(p)

n = snk.loads(sys.argv[1])
g = snk.StateGraph(n)
for i in g :
    if i % 200 == 0 :
        sys.stderr.write("\r%s states" % len(g))
        sys.stderr.flush()
    m = g.net.get_marking()
    if not g.successors() :
        print "\rDEADLOCK", i
        printstate(m)
    elif any(".crossing" in p for p in m) and not 0 in m("gate().state") :
        print "\rUNSAFETY", i
        printstate(m)


print "\r%s states" % len(g)
if len(g) < 100 :
    g.draw("%s.ps" % sys.argv[1], edge_attr=trans, node_attr=state, engine="dot")
