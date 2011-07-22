CTYPES=../../ctypes

all: mkln

mkln:
	ln -sf $(CTYPES)/ctypes_ext.pxd .
	ln -sf $(CTYPES)/ctypes_ext.pyx .
	ln -sf $(CTYPES)/ctypes.h .
	ln -sf $(CTYPES)/libctypesd.so .
	ln -sf $(CTYPES)/libctypes.so .

clean:
	rm -f ctypes_ext.pxd ctypes_ext.pyx ctypes.h libctypesd.so libctypes.so *~

.PHONY: mkln