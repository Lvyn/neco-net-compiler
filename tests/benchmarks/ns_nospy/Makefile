include ../../common/Makefile.inc

CASES=10
COUNT=1
COMMON=../../common/

# INITIALIZE=export PYTHONPATH=$(PYTHONPATH) ;\
# 	   export LD_LIBRARY_PATH=$(LIBPATH);\
# 	   export CC=llvm-gcc ;\
# 	   export LD=llvm-gcc ;\

INITIALIZE=export PYTHONPATH=$(PYTHONPATH) ;\
	   export LD_LIBRARY_PATH=$(LIBPATH);\
	   cp model$(COUNT).pnml model.pnml

all: run

run: clean
	@$(INITIALIZE) ;\
	$(PYTHON) $(TESTRUNNER) --statespace --backend $(LANG) $(_OPTS) -I$(COMMON)

bench: clean
	@ $(INITIALIZE) ;\
	file=$(LANG)_bench_$(BENCH_BEGIN)_$(BENCH_END).results ;\
	echo -n > $$file ;\
	for i in `seq $(BENCH_BEGIN) $(INCR) $(BENCH_END)`; do \
		echo "count: $$i" ;\
		cp model$$i.pnml model.pnml ;\
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
		$(PYTHON) $(COMMON)parse_netcompiler.py -no $$tmp -o $$opt_tmp >> $$file ;\
	done

prof: clean
	@$(INITIALIZE) ;\
	$(PYTHON) $(TESTRUNNER) --backend $(LANG) $(_OPTS) -I../../common --profile | less

clean:
	@ rm -rf *.pyc *~ build net* model.* profile.stats \#*# ctypes.h

clean_results:
	@ rm -rf *.results .*.results

.PHONY: clean run bench prof
