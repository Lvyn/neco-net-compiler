#!/usr/bin/python
import sys

FATAL_ERROR = 2
FAILED = 1
SUCCESS = 0

class Marking(object):
    def __init__(self, init):
        self.data = { p : sorted(ms) for p, ms in init.iteritems() }

    def __repr__(self):
        return repr(self.data)

    def __str__(self):
        return str(self.data)

    def __eq__(self, other):
        return self.data == other.data


class MarkingSet(object):
    def __init__(self, init):
        self.data = set( [ Marking(d) for d in init ] )

    def add(self, marking):
        self.data.add(marking)

    def __contains__(self, marking):
        for m in self.data:
            if marking == m:
                return True
        return False

    def __eq__(self, other):
        if len(self.data) != len(other.data):
            return False
        for marking in other.data:
            if not marking in self:
                return False
        return True

    def __str__(self):
        return str(self.data)

    def __repr__(self):
        return repr(self.data)

def usage():
    print sys.argv[0] + " TESTNAME EXPECTED RESULT"

def main():
    if len(sys.argv) != 4:
        usage()
        exit(FATAL_ERROR)

    testname = sys.argv[1]
    expect = sys.argv[2]
    result = sys.argv[3]

    try:
        expect_file = open(expect, 'r')
        result_file = open(result, 'r')
    except IOError as e:
        print >> sys.stderr, str(e)
        exit(FATAL_ERROR)
    try:
        expect_markings = MarkingSet(eval(expect_file.read()))

    except SyntaxError as e:
        print >> sys.stderr, "Syntax error in file {}, please check this file.".format(expect)
        print >> sys.stderr, str(e)
        exit(FATAL_ERROR)

    try:
        result_markings = MarkingSet(eval(result_file.read()))
    except SyntaxError as e:
        print >> sys.stderr, "Syntax error in file {}, please check this file.".format(result)
        print >> sys.stderr, str(e)
        exit(FATAL_ERROR)

    if not expect_markings == result_markings:
        error = open(testname + ".err", 'w')
        print >> error, "test %s failed..." % testname
        print >> error, "expected: "
        print >> error, expect_markings
        print >> error, "got: "
        print >> error, result_markings
        exit(FAILED)
    exit(SUCCESS)


if __name__ == '__main__':
    main()
