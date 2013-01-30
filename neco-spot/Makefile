CXX=g++
LIBS= -lpython2.7 /usr/local/lib/libspot.a /usr/local/lib/libbdd.a -lboost_program_options
LIBPATHS=-L.
INCLUDES= -I/usr/include/python2.7 -I/usr/local/include/spot -L../ctypes/
LDFLAGS= $(LIBPATHS) $(LIBS)
CXXFLAGS=$(INCLUDES)
PWD=$(shell pwd)
EXEC=necospotcli

SRC=main.cpp neco_model.cpp neco_state.cpp neco_succiter.cpp neco_tgba.cpp ctypes.cpp
OBJS=main.o neco_model.o neco_state.o neco_succiter.o neco_tgba.o ctypes.o

DEBUG ?= 0
ifeq ($(DEBUG), 1)
	CXXFLAGS += -ggdb -DNECO_TRACE
else
	CXXFLAGS += -O2
endif

all: $(OBJS)
	$(CXX) $(CXXFLAGS) -o $(EXEC) $^ $(LDFLAGS)
	ln -sf $(PWD)/$(EXEC) ../bin/
	ln -sf $(PWD)/neco-spot ../bin/

symlinks:
	ln -s ../ctypes/ctypes.h .

%.o: %.cpp
	$(CXX) $(CXXFLAGS) -o $@ -c $<

clean:
	rm -f *.o a.out $(EXEC)

.PHONY: all $(SRC)
