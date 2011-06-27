include ../../common/Makefile.inc

INITIALIZE=export PYTHONPATH=$(PYTHONPATH) ;\
	   export LD_LIBRARY_PATH=$(LIBPATH);\
	   export CC=gcc ;\
	   export LD=gcc

LANG=python
PFE=

all: run

run: clean
	@$(INITIALIZE) ;\
	$(PYTHON) $(TESTRUNNER) --lang $(LANG) $(PFE) $(_OPTS) -I../../common

clean:
	@ rm -rf net.* build *~ ctypes.h spec.pyc