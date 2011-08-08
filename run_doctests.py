import doctest, sys, glob, os, os.path

packages = [ 'neco',
             'neco.core',
             'neco.backends',
             'neco.backends.python',
             'neco.backends.cython',
             'neco.opt' ]

def search_modules(package_str):
    """ Search all modules of a package.

    @param package_str: dotted package name, ex. foo.bar
    @type package_str: C{str}
    """
    l = package_str.split('.')
    l.append('*.py')
    path = apply(os.path.join, l)
    python_file_paths = glob.glob(path)
    return [ mod.replace('.py', '').replace('/__init__', '').replace(os.sep, '.')
             for mod in python_file_paths ]


tests = 0
failed = 0

def test (module) :
    global tests, failed
    tests += 1
    print "Testing '%s'" % module.__name__
    ret_code, t = doctest.testmod(module, # verbose=True,
                                  optionflags=doctest.NORMALIZE_WHITESPACE
                                  | doctest.REPORT_ONLY_FIRST_FAILURE
                                  | doctest.ELLIPSIS)
    if ret_code != 0:
        failed += 1

def run_tests():
    for package in packages:
        modules = search_modules(package)
        for module in modules:
            try :
                __import__(module)
                test(sys.modules[module])
            except :
                print "  Could not test %r:" % module
                c, e, t = sys.exc_info()
                print "    %s: %s" % (c.__name__, e)
    print
    print "{tests} files tested, {failed} failed.".format(tests=(tests - failed), failed=failed)
    print

if __name__ == '__main__':
    run_tests()

