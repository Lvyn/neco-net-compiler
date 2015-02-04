#!/usr/bin/env python

from Cython.Distutils import build_ext
from distutils.command.install_lib import install_lib
from distutils.core import setup, setup
from distutils.extension import Extension
from snakes.lang.asdl import compile_asdl
import sys, os, subprocess, shutil

ENABLE_NECO_SPOT_OPTION='enable-neco-spot'
DEV_OPTION='dev'
BUILD_OPTION='build'
INSTALL_OPTION='install'

scripts=['bin/neco-compile', 'bin/neco-explore']

def usage():
    print "usage TODO"

def silent_symlink(source, link):
    try:        os.symlink(source, link)
    except:     pass

def gen_asdl():
    print 'generating ASDL'
    compile_asdl('neco/asdl/properties.asdl',   'neco/asdl/properties.py')
    compile_asdl('neco/asdl/netir.asdl',        'neco/asdl/netir.py')
    compile_asdl('neco/asdl/cython.asdl',       'neco/asdl/cython.py')
    compile_asdl('neco/asdl/cpp.asdl',          'neco/asdl/cpp.py')
    compile_asdl('neco/asdl/stub.asdl',         'neco/asdl/stub.py')


def create_local_symlinks():
    print 'creating local symlinks'
    os.chdir('neco-spot')
    silent_symlink('../neco/ctypes/ctypes.h',      'ctypes.h')
    silent_symlink('../neco/ctypes/ctypes.cpp',    'ctypes.cpp')
    os.chdir('..')

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

def has_prefix():
    for i, opt in enumerate(sys.argv):
        if opt.find('--prefix') == 0:
            return True
    return False

if (DEV_OPTION in sys.argv):
    gen_asdl()
    create_local_symlinks()
    exit(0)

if (BUILD_OPTION in sys.argv) or (INSTALL_OPTION in sys.argv):
    gen_asdl()
    create_local_symlinks()
else:
    usage()
    exit(1)

if (INSTALL_OPTION in sys.argv and not has_prefix()):
    sys.argv.append('--prefix=~/.local/')

if (ENABLE_NECO_SPOT_OPTION in sys.argv):
    sys.argv.remove(ENABLE_NECO_SPOT_OPTION)

    print "Building neco-spot"
    os.chdir('neco-spot')
    res = subprocess.call(['make'])
    os.chdir('..')
    if (res != 0):
        print >> sys.stderr, "error while building neco-spot"
        exit(2)

    try:
        shutil.copy('neco-spot/necospotcli', 'bin/neco-spot')
    except IOError:
        print >> sys.stderr, "unable to copy 'neco-spot/necospotcli' to 'bin/neco-spot'"
        exit(1)
    scripts.extend(['bin/neco-check', 'bin/neco-spot', 'bin/neco-check-spot'])

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
                'neco.backends.python.priv',
                'neco.backends.cython',
                'neco.backends.cython.priv',
                'neco.backends.stub',
                'neco.backends.stub.priv',],
      package_data={'neco.ctypes' : ['include.pxd',
                                     'include.pyx',
                                     'include_no_stats.pyx',
                                     'ctypes_ext.pxd',
                                     'ctypes.h',
                                     'ctypes_spec.h',
                                     'ctypes_ext.h',
                                     'ctypes.cpp'] },
      cmdclass={'build_ext':build_ext},
      ext_modules=[Extension('neco.ctypes.ctypes_ext',
                             ['neco/ctypes/ctypes_ext.pyx',
                              'neco/ctypes/ctypes.cpp'],
                             language='c++')],
      license='LGPL',
      scripts=scripts)

prefix = has_non_std_prefix()
if prefix:
    if prefix[-1] != '/':
        prefix += '/'

    print sys.version_info
    py_version = '{}.{}'.format(sys.version_info.major, sys.version_info.minor)
    if py_version != '2.7':
        exit(-1)

    print
    print '[W] You are using a non standard prefix ({}) please add the following lines to your .bashrc file:'.format(prefix)
    print
    print 'export PATH=$PATH:{}bin'.format(prefix)
    print 'export PYTHONPATH=$PYTHONPATH:{}lib/python{}/site-packages'.format(prefix, py_version)
    print 'export NECO_INCLUDE={prefix}lib/python{py_version}/site-packages/neco/ctypes:{prefix}lib/python{py_version}/site-packages/neco/backends/python:{prefix}lib/python{py_version}/site-packages'.format(prefix=prefix, py_version=py_version)
    print 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$NECO_INCLUDE'
    print

