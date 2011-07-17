import shelve

_dict_name = '/tmp/neco_{h}'.format(h=hash('neco'))

def set(**kwargs):
    d = shelve.open(_dict_name)
    for (name, value) in kwargs.iteritems():
        d[name] = value
    d.close()

def get(name):
    d = shelve.open(_dict_name)
    try:
        res = d[name]
    except KeyError:
        d.close()
        raise RuntimeError('bad configuration, key \'{key}\' missing'.format(key=name))
    d.close()
    return res

