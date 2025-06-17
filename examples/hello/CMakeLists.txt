cmake_minimum_required(VERSION 3.10)
project(hello)

include(../../basic.cmake)

add_executable(app app.c)
install(TARGETS app RUNTIME DESTINATION bin COMPONENT app)

add_library(hello STATIC hello.h hello.c)
install(TARGETS hello ARCHIVE DESTINATION lib COMPONENT hello)
install(FILES hello.h DESTINATION inc COMPONENT hello)