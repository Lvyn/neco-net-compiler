""" Module that manages configuration options.

Every option is stored in a global dictionnary and made
available between modules. The communication is done
using a temporary file C{/tmp/neco_{h}_{pid}} where {h} is the
hash value of C{'neco'} and pid the current proccess id.

"""

import shelve, os

_default_options_ = [
    ('backend', 'python'),
    ('profile', False),
    ('optimize', False),
    ('optimize_flow', False),
    ('bit_packing', False),
    ('debug', False),
    ('dump_enabled', True),
    ('search_paths', ['.']),
    ('trace_calls', False),
    ('trace_file', 'trace'),
    ('imports', []),
    ('model', []),
    ('pid_normalization', False)
]

_dict_name_ = '/tmp/neco_{}_{}'.format(hash('neco'), os.getpid())

def set(**kwargs):
    """ Set options.

    >>> set(ultimate_answer=42, enigma=23)
    >>> get('ultimate_answer')
    42
    >>> get('enigma')
    23
    """
    d = shelve.open(_dict_name_)
    for (name, value) in kwargs.iteritems():
        d[name] = value
    d.close()

def get(name):
    """ Get option value.

    >>> set(ultimate_answer=42, enigma=23)
    >>> get('ultimate_answer')
    42
    >>> get('enigma')
    23
    """
    d = shelve.open(_dict_name_)
    try:
        res = d[name]
    except KeyError:
        d.close()
        raise RuntimeError('bad configuration, key \'{key}\' missing'.format(key=name))
    d.close()
    return res

def dump_config():
    d = shelve.open(_dict_name_)
    for key, value in d.iteritems():
        print '{!s} : {!s}'.format(key, value)
    d.close()

def init():
    d = shelve.open(_dict_name_)
    for key, value in _default_options_:
        if not d.has_key(key):
            d[key] = value
    d.close()



def uninit():
    try:
        os.remove(_dict_name_)
    except OSError:
        pass

init()

import atexit
atexit.register(uninit)
