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

all: ctypes tests

ctypes:
	cd $(CTYPES_DIR); $(MAKE)

tests: ctypes
	cd $(TESTS_COMMON_DIR); $(MAKE)
	cd $(TESTS_BASICS_DIR); $(PYTHON) gen_makefile.py

clean: cleandoc
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

.PHONY: ctypes