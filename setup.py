#!/usr/bin/env python

from distutils.core import setup
from snakes.lang.asdl import compile_asdl

from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

import sys

def gen_asdl():
    print "generating ASDL"
    compile_asdl('neco/asdl/properties.asdl', 'neco/asdl/properties.py')
    compile_asdl('neco/asdl/netir.asdl',      'neco/asdl/netir.py')
    compile_asdl('neco/asdl/cython.asdl',     'neco/asdl/cython.py')

std_paths = ['/usr', '/usr/', '/usr/local', '/usr/local/']
def has_non_std_prefix():
    for i, opt in enumerate(sys.argv):
        if opt.find('--prefix') == 0:
            if len(opt) > 8 and opt[8] == '=':
                path = opt[9:]
            else:
                path = sys.argv[i+1]
            if path not in std_paths:
                return path
    return None

if ('dev' in sys.argv):
    gen_asdl()
    exit(0)

if ('build' in sys.argv) or ('install' in sys.argv):
    gen_asdl()

setup(name='Neco',
      version='0.1',
      description='Neco Net Compiler',
      author='Lukasz Fronc',
      author_email='lfronc@ibisc.univ-evry.fr',
      url='http://code.google.com/p/neco-net-compiler/',
      packages=['neco',
                'neco.asdl',
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
    print "export PATH=$PATH:{}bin".format(prefix)
    print "export NECO_INCLUDE={}lib/python{}/site-packages/neco/ctypes".format(prefix, py_version)
    print "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$NECO_INCLUDE"
    print
