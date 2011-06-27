include ../../common/Makefile.inc

# INITIALIZE=export PYTHONPATH=$(PYTHONPATH) ;\
# 	   export LD_LIBRARY_PATH=$(LIBPATH);\
# 	   export CC=llvm-gcc ;\
# 	   export LD=llvm-gcc ;\
# 	   abcd --cpp --pnml=model.pnml ns.abcd

INITIALIZE=export PYTHONPATH=$(PYTHONPATH) ;\
	   export LD_LIBRARY_PATH=$(LIBPATH);\
	   abcd --pnml=model.pnml ns.abcd

CASES=10
COMMON=../../common/
PFE=
all: run

run: clean
	@$(INITIALIZE) ;\
	$(PYTHON) $(TESTRUNNER) --lang $(LANG) $(_OPTS) $(PFE) -I../../common

bench: clean
	@ $(INITIALIZE) ;\
	file=$(LANG)_bench.results ;\
	echo -n > $$file ;\
	raw_file=.$(LANG)_bench_raw.results ;\
	opt_raw_file=.$(LANG)_bench_opt_raw.results ;\
	echo -n > $$raw_file ;\
	echo -n > $$opt_raw_file ;\
	for j in `seq 1 $(CASES)`; do \
		echo "case: $$j" ;\
		echo "case: $$j" >> $$raw_file ;\
		echo "case: $$j" >> $$opt_raw_file ;\
		echo "no opt" ;\
		sleep 1;\
		$(PYTHON) $(TESTRUNNER) --statespace --backend $(LANG) -I$(COMMON) >> $$raw_file ;\
		echo "opt" ;\
		sleep 1;\
		$(PYTHON) $(TESTRUNNER) --statespace --backend $(LANG) --opt -I$(COMMON) >> $$opt_raw_file ;\
	done;\
	tmp=.tmp$$raw_file ;\
	opt_tmp=.tmp$$opt_raw_file ;\
	echo "count: $$i" > $$tmp ;\
	echo "count: $$i" > $$opt_tmp ;\
	egrep "case|compilation|exploration|len" $$raw_file >> $$tmp ;\
	egrep "case|compilation|exploration|len" $$opt_raw_file >> $$opt_tmp ;\
	$(PYTHON) $(COMMON)parse_netcompiler.py -no $$tmp -o $$opt_tmp >> $$file

prof: clean
	@$(INITIALIZE) ;\
	$(PYTHON) $(TESTRUNNER) --backend $(LANG) $(_OPTS) -I../../common --profile | less

clean:
	@ rm -rf *.pyc *~ build net* model.* profile.stats \#*# ctypes.h

clean_results:
	@ rm -rf *.results .*.results

.PHONY: clean run bench prof
