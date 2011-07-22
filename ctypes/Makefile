CFLAGS=-shared -fPIC -Wall -DNDEBUG -g
CFLAGS_DEBUG=-shared -fPIC -Wall -g
CC=gcc

all: ctypes_ext ctypes_extd

ctypes:
	$(CC) $(CFLAGS) -o libctypes.so ctypes.c ;\

ctypesd:
	$(CC) $(CFLAGS_DEBUG) -o libctypesd.so ctypes.c ;\


ctypes_ext: ctypes
	python ./build.py

ctypes_extd: ctypesd
	python ./build.py -prof

.PHONY: ctypes ctypesd ctypes_ext

clean:
	rm -rf *~ *.so *.pyc rm ctypes_ext.c build/ ctypes_extd.*