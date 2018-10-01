SPOT_BASE?=/usr/local
LIBS= -lpython2.7 -L$(SPOT_BASE)/lib -lspot -lbddx -lboost_program_options
LIBPATHS=-L. -L/usr/local/lib -L$(SPOT_BASE)/lib -L../ctypes/
INCLUDES= -I/usr/include/python2.7 -I$(SPOT_BASE)/include/
LDFLAGS= $(LIBPATHS) $(LIBS)
PWD=$(shell pwd)
EXEC=necospotcli

SRC=main.cpp neco_model.cpp neco_state.cpp neco_succiter.cpp neco_tgba.cpp ctypes.cpp
OBJS=main.o neco_model.o neco_state.o neco_succiter.o neco_tgba.o ctypes.o

DEBUG ?= 0
ifeq ($(DEBUG), 1)
	CXXFLAGS = -ggdb -DNECO_TRACE -std=c++14
else
	CXXFLAGS = -O3 -std=c++14
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
