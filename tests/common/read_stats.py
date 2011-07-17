import cProfile

#!/usr/bin/env python
# encoding: utf-8
# filename: profile.py

import pstats, cProfile

s = pstats.Stats("profile.stats")
s.strip_dirs().sort_stats("time").print_stats()
