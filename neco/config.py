""" Module that manages configuration options.

Every option is stored in a global dictionnary and made
available between modules. The communication is done
using a temporary file C{/tmp/neco_{h}} where {h} is the
hash value of C{'neco'}.

"""

import shelve

_default_options_ = [
    ('backend', 'python'),
    ('profile', False),
    ('optimise', False),
    ('optimise_flow', False),
    ('debug', False),
    ('additional_search_paths', ['.']),
    ('trace_calls', False),
    ('imports', []),
]

_dict_name_ = '/tmp/neco_{h}'.format(h=hash('neco'))

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



def init():
    d = shelve.open(_dict_name_)
    for key, value in _default_options_:
        if not d.has_key(key):
            d[key] = value
    d.close()

init()
