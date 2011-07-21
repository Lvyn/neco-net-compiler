include ../../common/Makefile.inc

INITIALIZE=export PYTHONPATH=$(PYTHONPATH) ;\
	   export LD_LIBRARY_PATH=$(LIBPATH);\
	   export CC=gcc ;\
	   export LD=gcc

LANG=cython

all: run

run: clean
	@$(INITIALIZE) ;\
	$(PYTHON) $(TESTRUNNER) -l $(LANG) $(_OPTS) -I../../common

clean:
	@ rm -rf net.* build *~ ctypes.h spec.pyc base_net.h