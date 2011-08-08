""" Module that manages configuration options.

Every option is stored in a global dictionnary and made
available between modules. The communication is done
using a temporary file C{/tmp/neco_{h}} where {h} is the
hash value of C{'neco'}.

"""

import shelve

_dict_name = '/tmp/neco_{h}'.format(h=hash('neco'))

def set(**kwargs):
    """ Set options.

    >>> set(ultimate_answer=42, enigma=23)
    >>> get('ultimate_answer')
    42
    >>> get('enigma')
    23
    """
    d = shelve.open(_dict_name)
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
    d = shelve.open(_dict_name)
    try:
        res = d[name]
    except KeyError:
        d.close()
        raise RuntimeError('bad configuration, key \'{key}\' missing'.format(key=name))
    d.close()
    return res

