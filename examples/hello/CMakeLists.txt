cmake_minimum_required(VERSION 3.10)
project(hello)

message(STATUS "CMAKE_CROSSCOMPILING: ${CMAKE_CROSSCOMPILING}")
message(STATUS "CMAKE_SYSTEM_NAME: ${CMAKE_SYSTEM_NAME}")
message(STATUS "CMAKE_SYSTEM_PROCESSOR: ${CMAKE_SYSTEM_PROCESSOR}")

include(../../basic.cmake)

add_executable(app app.c)
install(TARGETS app RUNTIME DESTINATION bin COMPONENT app)

add_library(hello STATIC hello.h hello.c)
install(TARGETS hello ARCHIVE DESTINATION lib COMPONENT hello)
install(FILES hello.h DESTINATION inc COMPONENT hello)