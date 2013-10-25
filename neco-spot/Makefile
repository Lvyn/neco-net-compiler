SPOT_BASE?=/usr/local
LIBS= -lpython2.7 $(SPOT_BASE)/lib/libspot.a -lbdd -lboost_program_options
LIBPATHS=-L. -L/usr/local/lib -L$(SPOT_BASE)/lib -L../ctypes/
INCLUDES= -I/usr/include/python2.7 -I$(SPOT_BASE)/include/spot -I$(SPOT_BASE)/include/ -I/usr/local/include/spot
LDFLAGS= $(LIBPATHS) $(LIBS)
PWD=$(shell pwd)
EXEC=necospotcli

SRC=main.cpp neco_model.cpp neco_state.cpp neco_succiter.cpp neco_tgba.cpp ctypes.cpp
OBJS=main.o neco_model.o neco_state.o neco_succiter.o neco_tgba.o ctypes.o

DEBUG ?= 0
ifeq ($(DEBUG), 1)
	CXXFLAGS = -ggdb -DNECO_TRACE
else
	CXXFLAGS = -O3
endif

all: $(OBJS)
	$(CXX) $(CXXFLAGS) $(INCLUDES) -o $(EXEC) $^ $(LDFLAGS)

symlinks:
	ln -s ../ctypes/ctypes.h .

%.o: %.cpp
	$(CXX) $(CXXFLAGS) $(INCLUDES) -o $@ -c $<

clean:
	rm -f *.o a.out $(EXEC)

.PHONY: all $(SRC)
