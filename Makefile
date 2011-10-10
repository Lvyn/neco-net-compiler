PYTHON=python
TESTS_COMMON_DIR = tests/common
TESTS_BASICS_DIR = tests/basics
CTYPES_DIR = ctypes
CLEAN_SUBDIRS = ctypes \
		tests/common \
		tests/benchmarks/ns_nospy \
		tests/benchmarks/ns \
		tests/benchmarks/philo \
		tests/benchmarks/railroad \
		tests/basics

all: asdl tests

ctypes:
	cd $(CTYPES_DIR); $(MAKE)

asdl:
	$(PYTHON) -m snakes.lang.asdl --output=neco/core/netir_gen.py asdl/netir.asdl
	$(PYTHON) -m snakes.lang.asdl --output=neco/backends/cython/cyast_gen.py asdl/cython.asdl

tests:
	cd $(TESTS_COMMON_DIR); $(MAKE)
	cd $(TESTS_BASICS_DIR); $(PYTHON) gen_makefile.py

clean_results:
	for i in $(CLEAN_SUBDIRS); do \
	echo "cleaning in $$i..."; \
	(cd $$i; $(MAKE) clean_results 2> /dev/null); done;

doc: 	cleandoc
	epydoc --config doc/epydoc.conf -v

cleandoc:
	rm -rf doc/api

.PHONY: ctypes asdl