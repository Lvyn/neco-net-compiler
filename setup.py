#!/usr/bin/env python

from distutils.core import setup
from snakes.lang.asdl import *

from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

import sys

def compile_asdl(infilename, outfilename):
    infile = open(infilename, 'r')
    outfile = open(outfilename, 'w')

    scanner = asdl.ASDLScanner()
    parser = asdl.ASDLParser()
    tokens = scanner.tokenize(infile.read())
    node = parser.parse(tokens)

    outfile.write(("# this file has been automatically generated running:\n"
                   "# %s\n# timestamp: %s\n\n") % (" ".join(sys.argv),
                                                   datetime.datetime.now()))
    outfile.write(CodeGen().python(node))
    outfile.close()
    infile.close()

def gen_neco_asdl():
    compile_asdl('neco/asdl/cython.asdl',     'neco/asdl/cython.py')
    compile_asdl('neco/asdl/netir.asdl',      'neco/asdl/netir.py')
    compile_asdl('neco/asdl/properties.asdl', 'neco/asdl/properties.py')

if ('build' in sys.argv) or ('install' in sys.argv):
    gen_neco_asdl()

if ('dev' in sys.argv):
    gen_neco_asdl()
    exit(0)

print sys.argv

def has_non_std_prefix():
    def check_path(path):
        return path not in ['/usr', '/usr/', '/usr/local', '/usr/local/']

    for i, opt in enumerate(sys.argv):
        if opt.find('--prefix') == 0:
            if len(opt) > 8 and opt[8] == '=':
                path = opt[9:]
            else:
                path = sys.argv[i+1]
            if check_path(path):
                return path
    return None

setup(name='Neco',
      version='0.1',
      description='Neco Net Compiler',
      author='Lukasz Fronc',
      author_email='lfronc@ibisc.univ-evry.fr',
      url='http://code.google.com/p/neco-net-compiler/',
      packages=['neco',
                'neco.core',
                'neco.ctypes',
                'neco.backends',
                'neco.backends.python',
                'neco.backends.cython',],
      package_data={'neco.ctypes' : ['include.pyx',
                                     'include_no_stats.pyx',
                                     'ctypes_ext.pxd',
                                     'ctypes.h'] },
      cmdclass={'build_ext':build_ext},
      ext_modules=[Extension('neco.ctypes.libctypes', ['neco/ctypes/ctypes.c']),
                   Extension("neco.ctypes.ctypes_ext", ["neco/ctypes/ctypes_ext.pyx"],
                             extra_link_args=["-lctypes", "-L./neco/ctypes/"])],
      license='LGPL',
      scripts=['bin/neco-check',
               'bin/neco-compile',
               'bin/neco-explore'])

prefix = has_non_std_prefix()
if prefix:
    if prefix[-1] != '/':
        prefix += '/'

    print sys.version_info
    py_version = "{}.{}".format(sys.version_info.major, sys.version_info.minor)
    if py_version != '2.7':
        exit(-1)

    print
    print "[W] You are using a non standard prefix ({}) please add the following lines to your .bashrc file:".format(prefix)
    print
    print "export NECO_INCLUDE={}lib/python{}/site-packages/neco/ctypes".format(prefix, py_version)
    print "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$NECO_INCLUDE"
    print
