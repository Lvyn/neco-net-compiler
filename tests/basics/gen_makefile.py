
import os

lst = []
for d in os.listdir('.'):
    if os.path.isdir(d) and d[0] != '.':
        lst.append(d)


clean_subdirs = '\t\\\n'.join(lst)

f = open('Makefile', 'w')
f.write('CLEAN_SUBDIRS = ')
f.write(clean_subdirs)
f.write("""
all:

clean:
	for i in $(CLEAN_SUBDIRS); do \\
        echo \"clean $$i...\"; \\
        (cd $$i; $(MAKE) $(MFLAGS) clean); done; \\
 	rm -rf *~ *.pyc
""")
f.close()


# CLEAN_SUBDIRS = basic_1 \
# 	tuple_match_1 \
# 	tuple_match_2 \
# 	tuple_match_3 \
# 	tuple_match_4


# all:

# clean:
# 	@for i in $(CLEAN_SUBDIRS); do \
# 	echo "clearing in $$i..."; \
# 	(cd $$i; $(MAKE) $(MFLAGS) clean); done; \
# 	rm -rf *~ *.pyc
