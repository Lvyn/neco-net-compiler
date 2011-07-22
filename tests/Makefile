CLEAN_SUBDIRS = basics benchmarks

all:

clean:
	@for i in $(CLEAN_SUBDIRS); do \
	echo "clearing in $$i..."; \
	(cd $$i; $(MAKE) $(MFLAGS) clean); done; \
	rm -rf *~ *.pyc
