#!/usr/bin/python

import argparse, shutil
from distutils.core import setup
from distutils.extension import Extension
from Cython.Distutils import build_ext

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-prof', dest='prof', action='store_true', default=False,
                        help='enable profiling support')
    args = parser.parse_args()


    if args.prof:
        shutil.copyfile("ctypes_ext.pxd", "ctypes_extd.pxd")

        ext_pyx  = open("ctypes_ext.pyx", "r")
        extd_pyx = open("ctypes_extd.pyx", "w")

        extd_pyx.write("# cython: profile=True\n")
        extd_pyx.write("cimport ctypes_extd as ctypes_ext\n\n")
        for i,line in enumerate(ext_pyx):
            if i > 1:
                extd_pyx.write(line)

        ext_pyx.close()
        extd_pyx.close()

        setup(name="ctypes_extd",
              cmdclass={'build_ext': build_ext},
              ext_modules=[Extension("ctypes_extd", ["ctypes_extd.pyx"],
                                     extra_link_args=["-lctypesd", "-L."])],
              script_args=["build_ext", "--inplace"])
    else:
        # build extensions
        setup(name="ctypes_ext",
              cmdclass={'build_ext': build_ext},
              ext_modules=[Extension("ctypes_ext", ["ctypes_ext.pyx"],
                                     extra_link_args=["-lctypes", "-L."])],
              script_args=["build_ext", "--inplace"])

