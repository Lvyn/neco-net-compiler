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

tests:
	cd $(TESTS_COMMON_DIR); $(MAKE)
	cd $(TESTS_BASICS_DIR); $(PYTHON) gen_makefile.py

asdl:
	$(PYTHON) -m snakes.lang.asdl --output=asdl/cyast_gen.py asdl/cython.asdl
	$(PYTHON) -m snakes.lang.asdl --output=asdl/netir_gen.py asdl/netir.asdl
	ln -f asdl/cyast_gen.py neco/backends/cython/
	ln -f asdl/netir_gen.py neco/core/

clean: cleandoc
	rm -f neco/core/netir_gen.py asdl/netir_gen.py
	rm -f neco/backends/cython/cyast.py asdl/cyast_gen.py
	find -name *.pyc -exec rm {} \;
	find -name *~ -exec rm {} \;
	find -name \#*# -exec rm {} \;
	for i in $(CLEAN_SUBDIRS); do \
	echo "cleaning in $$i..."; \
	(cd $$i; $(MAKE) clean); done;
	cd $(TESTS_BASICS_DIR); rm Makefile

clean_results:
	for i in $(CLEAN_SUBDIRS); do \
	echo "cleaning in $$i..."; \
	(cd $$i; $(MAKE) clean_results 2> /dev/null); done;

doc: 	cleandoc
	epydoc --config doc/epydoc.conf -v

cleandoc:
	rm -rf doc/api

.PHONY: ctypes asdl