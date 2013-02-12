project(NECOSPOT)
cmake_minimum_required (VERSION 2.8)

include_directories(/usr/include/python2.7 /usr/local/include/spot)
link_directories(${CMAKE_CURRENT_SOURCE_DIR}../ctypes/)

set(SOURCE_FILES_PATH ".")
file(GLOB SOURCE_FILES *.cpp *.h *.inc *.inl)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS_DEBUG} -Wall -g -ggdb")

add_executable(necospotcli ${SOURCE_FILES})
target_link_libraries(necospotcli libspot.a libbdd.a python2.7 boost_program_options)
