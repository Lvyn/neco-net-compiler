#!/usr/bin/python

from StringIO import StringIO
from glob import glob
from snakes.nets import dot # @UnusedImport needed to rebuild markings
import compare
import neco
import os
import sys
import unittest


# Static config

try:
    env_includes = os.environ['NECO_INCLUDE'].split(":")
except KeyError:
    env_includes = []
    
backend_prefix = { 'python' : 'py_',
                   'cython' : 'cy_' }

def MarkingSet(state_space):
    """ Build a set of markings from a state space. """

    out = StringIO()
    out.write('[')
    for s in state_space:
        out.write(s.__dump__())
        out.write(', ')
    out.write(']')
    return compare.MarkingSet(eval(out.getvalue()))

class Entry:
    """ A file used as a test. """

    def __init__(self, name, module_name, ext, options):
        self.name = name
        self.module_name = module_name
        self.options = options
        self.ext = ext

    def __str__(self):
        return 'case {}, options: {}, ext: {}'.format(self.name, self.options, self.ext)

    def __repr__(self):
        return "Entry({!r}, {!r}, {!r}, {!r})".format(self.name, self.module_name, self.options, self.ext) 


class TestBackend(unittest.TestCase):
    """ Base class for backend testing. """
    
    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)
        for attr in self.__class__.__dict__.keys():
            if attr.startswith('test_'):
                tester = getattr(self.__class__, attr)
                tester.test = self
                
    def setUp(self):
        """ Disable stdout before test. """
        sys.stdout, self.oldstdout = StringIO(), sys.stdout
   
    def tearDown(self):
        """ Restore stdout after test. """
        sys.stdout = self.oldstdout
        pass

class PythonBackend(TestBackend):
    """ Class that will contain Python backend tests. """
    
    def __init__(self, methodName='runTest'):
        TestBackend.__init__(self, methodName)
        
class CythonBackend(TestBackend):
    """ Class that will contain Cython backend tests. """
    
    def __init__(self, methodName='runTest'):
        TestBackend.__init__(self, methodName)

class NecoTestCase(object):
    # Functor corresponding to a test. Creates a test from an Entry.

    def __init__(self, entry, config):
        self.entry = entry
        self.test = None
        self.config = config
        if entry.ext == '.py':
            self.load = self.load_net
        else:
            self.load = self.load_abcd
 

    def __call__(self):
        config = self.config
        model, expected = self.load()
        net = neco.compile_net(model, config)
        self.test.assert_(net, 'compilation_check')
        markings = MarkingSet(net.state_space())
        self.test.assertEqual(expected, markings, "correct markings")

    def load_net(self):
        module_file = self.entry.module_name
        out_file = self.entry.module_name + '.out'

        model = neco.load_snakes_net(module_file, 'net')
        expected = compare.MarkingSet(eval(open(out_file).read()))

        return model, expected

    def load_abcd(self):
        model_file = self.entry.module_name
        out_file = self.entry.module_name + '.out'

        pnml = neco.produce_pnml_file(model_file + '.abcd')
        model = neco.load_pnml_file(pnml, True)
        expected = compare.MarkingSet(eval(open(out_file).read()))

        return model, expected

    def compile_net(self):
        net = neco.compile_net(net=self.model)
        self.test.assert_(net, 'compilation_check')
        self.markings = MarkingSet(net.state_space())


def config_NOPT(backend, entry):
    return neco.config.Config(backend=backend,
                       search_paths=env_includes,
                       out_module=backend_prefix[backend] + entry.name + '_NOPT')

def config_OPT(backend, entry):
    return neco.config.Config(backend=backend,
                       search_paths=env_includes,
                       optimize=True,
                       out_module=backend_prefix[backend] + entry.name + '_OPT')
    
def config_BPACK(backend, entry):
    return neco.config.Config(backend=backend,
                       search_paths=env_includes,
                       optimize=True,
                       bit_packing=True,
                       out_module=backend_prefix[backend] + entry.name + '_BPACK')
    
def config_FLOW(backend, entry):
    return neco.config.Config(backend=backend,
                       search_paths=env_includes,
                       optimize=True,
                       bit_packing=True,
                       optimize_flow=True,
                       out_module=backend_prefix[backend] + entry.name + '_FLOW')

def populateTestCases():
    """ Function that adds tests based on files in current directory.
    
    Tests can be ignored bases on ignore list, this list may contain a backend names,
    option names, or extension names.
    
    """
    
    entries = []
    files = glob('case_*.py')
    files.extend(glob('case_*.abcd'))
    
    for entry in files:
        entry, ext = os.path.splitext(entry) # remove '.py'
        
        module_name = entry
        decode = entry.split('_') # split name
        prefix = decode.pop(0)
    
        # prefix must be case otherwise it is a regular file 
        if prefix != 'case':
            continue
    
        name = decode.pop(0)
        # remaining values are available options
        options = []
        for option in decode:
            if option in ['NOPT', 'OPT', 'FLOW', 'BPACK']:
                options.append(option)

        if options != []:
            entries.append(Entry(name, module_name, ext, decode))


    for entry in entries:
        for option in entry.options:

            if option == 'NOPT':
                config_py = config_NOPT('python', entry)
                config_cy = config_NOPT('cython', entry)
            elif option == 'OPT':
                config_py = config_OPT('python', entry)
                config_cy = config_OPT('cython', entry)
            elif option == 'BPACK':
                config_py = None
                config_cy = config_BPACK('cython', entry)
            elif option == 'FLOW':
                continue
                config_py = config_FLOW('python', entry)
                config_cy = config_FLOW('cython', entry)

            test_name = 'test_{case}_{option:_>5}'.format(case=entry.name, option=option)
            if config_py:
                setattr(PythonBackend, test_name, NecoTestCase(entry, config_py))

            if config_cy:
                setattr(CythonBackend, test_name, NecoTestCase(entry, config_cy))

if __name__ == '__main__':
    populateTestCases()
    if 'clean' in sys.argv:
        
        for entry in glob('cy_*.so'):
            os.remove(entry)
            
        for entry in glob('py_*.py'):
            os.remove(entry)
        
        for entry in glob('*.pyc'):
            os.remove(entry)
        
        exit(0)
        
        #os.remove(path)
    unittest.main(verbosity=2)
