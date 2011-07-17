import config

def debug_print(args):
    """ prints if debug flag is enabled

    @param *args:
    @type *args: C{}
    """
    if config.get('debug'):
        print(args)
