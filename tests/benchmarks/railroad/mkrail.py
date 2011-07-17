import sys

num = int(sys.argv[1])
src = ["const MAX = %d" % num]
for line in (l.rstrip() for l in open("railroad.abcd")) :
    if line.startswith("const MAX") :
        pass
    elif line.startswith("| track(") :
        break
    else :
        src.append(line)
src.extend("| track(%s)" % n for n in range(num))
print "\n".join(src)
