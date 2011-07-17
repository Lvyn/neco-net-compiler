include ../../common/Makefile.inc

# INITIALIZE=export PYTHONPATH=$(PYTHONPATH) ;\
# 	   export LD_LIBRARY_PATH=$(LIBPATH);\
# 	   export CC=llvm-gcc ;\
#            $(PYTHON) mkrail.py $(COUNT) > "model.abcd";\
# 	   abcd --cpp --pnml=model.pnml model.abcd

INITIALIZE=export PYTHONPATH=$(PYTHONPATH) ;\
	   export LD_LIBRARY_PATH=$(LIBPATH);\
	   abcd --cpp --pnml=model.pnml model.abcd

BENCH_BEGIN=1
BENCH_END=11
CASES=10

COMMON=../../common/

all: run

run: clean
	@$(INITIALIZE) ;\
	$(PYTHON) $(TESTRUNNER) --statespace --backend $(LANG) $(_OPTS) -I$(COMMON)


bench_opt: clean
	$(INITIALIZE) ;\
	file=$(LANG)_bench_$(BENCH_BEGIN)_$(BENCH_END).results ;\
	echo -n > $$file ;\
	for i in `seq $(BENCH_BEGIN) $(INCR) $(BENCH_END)`; do \
		echo "count: $$i" ;\
		$(PYTHON) mkrail.py $$i > model.abcd;\
		abcd --cpp --pnml=model.pnml model.abcd ;\
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

bench: clean
	$(INITIALIZE) ;\
	file=$(LANG)_bench_$(BENCH_BEGIN)_$(BENCH_END).results ;\
	echo -n > $$file ;\
	for i in `seq $(BENCH_BEGIN) $(INCR) $(BENCH_END)`; do \
		echo "count: $$i" ;\
		$(PYTHON) mkrail.py $$i > model.abcd;\
		abcd --cpp --pnml=model.pnml model.abcd ;\
		raw_file=$(LANG)_bench_raw_$(BENCH_BEGIN)_$(BENCH_END)_$$i.results ;\
		opt_raw_file=$(LANG)_bench_opt_raw_$(BENCH_BEGIN)_$(BENCH_END)_$$i.results ;\
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
		tmp=tmp.$$raw_file ;\
		opt_tmp=tmp.$$opt_raw_file ;\
		echo "count: $$i" > $$tmp ;\
		echo "count: $$i" > $$opt_tmp ;\
	 	egrep "case|compilation|exploration|len" $$raw_file >> $$tmp ;\
	 	egrep "case|compilation|exploration|len" $$opt_raw_file >> $$opt_tmp ;\
		$(PYTHON) $(COMMON)parse_netcompiler.py -no $$tmp -o $$opt_tmp >> $$file ;\
	done

bench_helena: clean
	$(INITIALIZE) ;\
	file=helena_bench_$(BENCH_BEGIN)_$(BENCH_END).results ;\
	rm -rf file ;\
	for i in `seq $(BENCH_BEGIN) $(BENCH_END)`; do \
		echo "count: $$i" ;\
		$(PYTHON) mkrail.py $$i > model.abcd ;\
		abcd --cpp --pnml=model.pnml model.abcd ;\
		$(PYTHON) rr2h.py model.pnml > model.lna ;\
		raw_file=helena_bench_raw_$$i.results ;\
		echo -n > $$raw_file ;\
		for j in `seq 1 $(CASES)`; do \
			echo "case: $$j" ;\
			echo "case: $$j" >> $$raw_file ;\
			helena --static-reductions=0 model.lna >> $$raw_file ;\
		done;\
	 	tmp=tmp.helena_bench$$i.results ;\
		echo "count: $$i" > $$tmp ;\
	 	rm model.pnml ;\
	 	egrep "case|compilation|space search|states stored \(at the end of the search\)" $$raw_file >> $$tmp ;\
		$(PYTHON) $(COMMON)parse_helena.py -f $$tmp >> $$file ;\
	done

prof: clean
	@$(INITIALIZE) ;\
	$(PYTHON) $(TESTRUNNER) --backend $(LANG) $(_OPTS) -I$(COMMON) --profile | less

helena:
	@$(INITIALIZE) ;\
	$(PYTHON) rr2h.py model.pnml > model.lna ;\
	helena --static-reductions=0 model.lna

clean:
	@rm -rf *.pyc *~ build net.* profile.stats \#*# ctypes.h

clean_results:
	@rm -rf *.results

.PHONY: clean run bench prof helena
