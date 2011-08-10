include ../../common/Makefile.inc

COUNT=10

# INITIALIZE=export PYTHONPATH=$(PYTHONPATH) ;\
# 	   export LD_LIBRARY_PATH=$(LIBPATH) ;\
# 	   export CC=llvm-gcc

INITIALIZE=export PYTHONPATH=$(PYTHONPATH) ;\
	   export LD_LIBRARY_PATH=$(LIBPATH)

BENCH_BEGIN=20
INCR=1
BENCH_END=36
CASES=10

COMMON=../../common/


all: run

run: clean
	@$(INITIALIZE) ;\
        $(PYTHON) mkphilo.py -t pnml -c $(COUNT) > "model.pnml" ;\
	$(PYTHON) $(TESTRUNNER) -l $(LANG) -e $(_OPTS) -I$(COMMON)

bench: clean
	@ $(INITIALIZE) ;\
	file=$(LANG)_bench_$(BENCH_BEGIN)_$(BENCH_END).results ;\
	echo -n > $$file ;\
	for i in `seq $(BENCH_BEGIN) $(INCR) $(BENCH_END)`; do \
		echo "count: $$i" ;\
	        $(PYTHON) mkphilo.py -t pnml -c $$i > "model.pnml" ;\
		raw_file=.$(LANG)_bench_raw_$(BENCH_BEGIN)_$(BENCH_END)_$$i.results ;\
		opt_raw_file=.$(LANG)_bench_opt_raw_$(BENCH_BEGIN)_$(BENCH_END)_$$i.results ;\
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


bench_opt: clean
	@ $(INITIALIZE) ;\
	file=$(LANG)_bench_$(BENCH_BEGIN)_$(BENCH_END).results ;\
	echo -n > $$file ;\
	for i in `seq $(BENCH_BEGIN) $(INCR) $(BENCH_END)`; do \
		echo "count: $$i" ;\
	        $(PYTHON) mkphilo.py -t pnml -c $$i > "model.pnml" ;\
		raw_file=$(LANG)_bench_raw_$(BENCH_BEGIN)_$(BENCH_END)_$$i.results ;\
		opt_raw_file=$(LANG)_bench_opt_raw_$(BENCH_BEGIN)_$(BENCH_END)_$$i.results ;\
		echo -n > $$raw_file ;\
		echo -n > $$opt_raw_file ;\
		for j in `seq 1 $(CASES)`; do \
			echo "case: $$j" ;\
			echo "case: $$j" >> $$raw_file ;\
			echo "case: $$j" >> $$opt_raw_file ;\
			echo "no opt" ;\
			echo "compilation time:  0.0" >> $$raw_file ;\
			echo "exploration time:  0.0" >> $$raw_file ;\
			echo "len visited = 0" >> $$raw_file ;\
			echo "opt" ;\
			sleep 1;\
			$(PYTHON) $(TESTRUNNER) --statespace --backend $(LANG) --opt -I$(COMMON) >> $$opt_raw_file ;\
		done;\
		tmp=tmp.$$raw_file ;\
		opt_tmp=tmp.$$opt_raw_file ;\
		echo "count: $$i" > $$tmp ;\
		echo "count: $$i" > $$opt_tmp ;\
	 	egrep "case|compilation|exploration|len" $$raw_file >> $$tmp ;\
	 	egrep "case|compilation|exploration|len" $$opt_raw_file >> $$opt_tmp ;\
		$(PYTHON) $(COMMON)parse_netcompiler.py -no $$tmp -o $$opt_tmp >> $$file ;\
	done


bench_helena: clean
	@ $(INITIALIZE) ;\
	file=helena_bench.results ;\
	rm -fr $$file ;\
	for i in `seq $(BENCH_BEGIN) $(INCR) $(BENCH_END)`; do \
		echo "count: $$i" ;\
		$(PYTHON) mkphilo.py -t lna -c $$i > model.lna ;\
		raw_file=helena_bench_raw_$$i.results ;\
		echo -n > $$raw_file ;\
		for j in `seq 1 $(CASES)`; do \
			echo "case: $$j" ;\
			echo "case: $$j" >> $$raw_file ;\
			helena --static-reductions=0 model.lna >> $$raw_file ;\
		done;\
		tmp=tmp.helena_bench$$i.results ;\
		echo "count: $$i" > $$tmp ;\
	 	egrep "case|compilation|space search|states stored \(at the end of the search\)" $$raw_file >> $$tmp ;\
		$(PYTHON) $(COMMON)parse_helena.py -f $$tmp >> $$file ;\
	done

prof: clean
	@$(INITIALIZE) ;\
        $(PYTHON) mkphilo.py -t pnml -c $(COUNT) > "model.pnml" ;\
	$(PYTHON) $(TESTRUNNER) -l $(LANG) $(_OPTS) -I$(COMMON) --profile

helena:
	@$(INITIALIZE) ;\
        $(PYTHON) mkphilo.py -t lna -c $(COUNT) > "model.lna" ;\
	helena --static-reductions=0 model.lna

clean:
	@ rm -rf *.pyc base_net.h *~ build net.* model.* profile.stats \#*# ctypes.h

clean_results:
	@ rm -rf *.results .*.results

.PHONY: clean run bench prof helena
