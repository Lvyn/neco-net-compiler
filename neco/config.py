
class Config(object):
    """ Class that manages configuration options.
    """
    
    def __init__(self, **kwargs):
        self.config = {}
        self.set_options(backend='python',
                         profile=False,
                         optimize=False,
                         optimize_flow=False,
                         bit_packing=False,
                         debug=False,
                         dump_enabled=False,
                         no_stats=True,
                         search_paths='.',
                         trace_calls=False,
                         trace_file='trace',
                         imports=[],
                         model=[],
                         normalize_pids=False,
                         out_module='net')
        self.set_options(**kwargs)
        
    def set_options(self, **kwargs):
        """ Set options.
        
        >>> config = Config()
        >>> config.config = {} # force reset
        >>> config.set_options(ultimate_answer=42, enigma=23)
        >>> config.ultimate_answer
        42
        >>> config.enigma
        23
        """
        for (name, value) in kwargs.iteritems():
            setattr(self, name, value)
            self.config[name] = value

    def dump(self):
        for key, value in self.config.iteritems():
            print '{!s} : {!s}'.format(key, value)
