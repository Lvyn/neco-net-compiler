import glob, re, os
import argparse

class Marking(object):
    def __init__(self):
        self.data = {}

    def add_token(self, place, token):
        try:
            place = self.data[place]
        except KeyError:
            self.data[place] = {}
            place = self.data[place]
        try:
            place[token] += 1
        except KeyError:
            place[token] = 1

    def create_place(self, place):
        try:
            self.data[place]
        except KeyError:
            self.data[place] = {}

    def __repr__(self):
        return str(self.data)

    def __str__(self):
        return str(self.data)

    def __eq__(self, other):
        return self.data == other.data

class MarkingSet(object):
    def __init__(self):
        self.data = set()

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

class FormatError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class FileReader(object):

    def __init__(self, filename):
        self.filename = filename
        self.line = 0
        self.file = open(filename, 'r')

    def readline(self):
        s = self.file.readline()
        self.line += 1
        return s

class SpecReader(FileReader):

    def __init__(self, filename):
        FileReader.__init__(self, filename)
        self.markings = MarkingSet()

    def read(self):
        check = self.readcheck()
        if check == 'markings':
            self.readmarkings()
        else:
            raise FormatError("unknown checking specification (%s) at line %d" % (check, self.line))

    def readcheck(self):
        s = self.readline()
        if self.line != 1:
            raise FormatError("check should be the first line")
        m = re.match(r"check\s*-\s*(?P<check>\w+)", s)
        if not m:
            raise FormatError("%s: syntax error at line %s" % (self.filename, self.line))
        check = m.group('check')
        return check

    def readmarkings(self):
        s = self.readline()
        m = re.match(r"count\s*-\s*(?P<count>[0-9]+)", s)
        if not m:
            raise FormatError("syntax error at line %s" % self.line)
        count = int(m.group('count'))
        for i in range(1, count+1):
            self.readmarking()

    def readmarking(self):
        marking = Marking()
        s = self.readline()
        m = re.match(r"begin marking", s)
        if not m:
            raise FormatError("%s: syntax error at line %s" % (self.filename, self.line))
        s = self.readline()
        while not re.match(r"end marking", s):
            m = re.match(r'(?P<place>[a-z0-9().#\'`]+)\s*-\s*(?P<tokens>(\'?\w*\'?\s)*)', s)
            if not m:
                raise FormatError("%s: syntax error at line %d" % (self.filename, self.line))
            place = m.group('place')
            tokens = re.split(r'\W+', m.group('tokens'))
            for token in tokens:
                if token == '':
                    marking.create_place(place)
                    continue
                marking.add_token(place, token)
            s = self.readline()
        self.markings.add(marking)

import subprocess

def run_test(module_name, lang='python', opt=False, pfe=False):
    print "Running test %s..." % module_name
    expected = module_name + '.out'
    got = module_name + '.res'

    args = ['python', "../../neco",
            '-m', module_name,
            '-dm', got,
            '-l', lang]
    if opt:
        args.append('--opt')
    if pfe:
        args.append('--pfe')

    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    p.wait()
    e_reader = SpecReader(expected)
    g_reader = SpecReader(got)
    e_reader.read()
    g_reader.read()
    if not e_reader.markings == g_reader.markings:
        print "test %s failed..." % module_name
        print "expected: "
        print e_reader.markings
        print "got: "
        print g_reader.markings

common_cases = ['basic_1',
                'basic_2',
                'basic_3',
                'basic_4',
                'basic_5',
                'basic_flow_1',
                'basic_flow_2',
                'basic_flow_3',
                'basic_flow_abcd_1',
                'basic_flow_abcd_2',
                'basic_flow_abcd_3',
                'basic_flow_abcd_4',
                'basic_flush_1',
                'match_1',
                'match_2',
                'match_3',
                'match_4',
                'match_5',
                'match_6',
                'basic_one_safe_1',
                'basic_one_safe_2']

flow_control_cases = [ 'basic_flow_1',
                       'basic_flow_2',
                       'basic_flow_3',
                       'basic_flow_abcd_1',
                       'basic_flow_abcd_2',
                       'basic_flow_abcd_3',
                       'basic_flow_abcd_4' ]


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Tests runner",
                                     argument_default=argparse.SUPPRESS,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--clean', '-C', dest='clean', action='store_true', default=False,
                        help='remove all produced files')
    parser.add_argument('--run-test', '-r', dest='run', action='append', default=[],
                        help='run a test case')
    parser.add_argument('--lang', '-l', dest='lang', action='append', default=[],
                        help='run a test case')
    args = parser.parse_args()
    langs = args.lang
    if len(langs) == 0:
        langs = ['Python']
    if args.clean:
        l = common_cases
        l.extend(flow_control_cases)
        tests = set(l)
        for test in tests:
            try:
                os.remove(test + '.res')
            except:
                pass
            try:
                os.remove(test + '.pyc')
            except:
                pass
            try:
                os.remove(test + '.pnml')
            except:
                pass
        try:
            os.remove('net.py')
        except: pass
        exit(0)
    elif args.run:
        for lang in langs:
            llang = lang.lower()
            print "*** {lang} without optimisations ***".format(lang=lang)
            for test in args.run:
                run_test(test, lang=llang)

            print
            print "*** {lang} with optimisations ***".format(lang=lang)
            for test in args.run:
                run_test(test, lang=llang, opt=True)


            exit(0)
    for lang in langs:
        llang = lang.lower()
        print "*** {lang} without optimisations ***".format(lang=lang)
        for test in common_cases:
            run_test(test, lang=llang)

        print
        print "*** {lang} with optimisations ***".format(lang=lang)
        for test in common_cases:
            run_test(test, lang=llang, opt=True)

        print
        print "*** {lang} with optimisations and flow control compression ***".format(lang=lang)
        for test in flow_control_cases:
            run_test(test, lang=llang, opt=True, pfe=True)
