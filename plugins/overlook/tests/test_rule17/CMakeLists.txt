cmake_minimum_required(VERSION 3.20)
project(test_rule17)
include("../../overlook.cmake")

#---------------------------------
# 原来版本的hello库，源码放在old目录
#---------------------------------
if(0)
add_library(hello STATIC
  ${CMAKE_CURRENT_SOURCE_DIR}/old/hello.h
  ${CMAKE_CURRENT_SOURCE_DIR}/old/hello.c
)
endif()

#---------------------------------
# 新版本的hello库，源码放在new目录
#---------------------------------
if(1)
add_library(hello STATIC
  ${CMAKE_CURRENT_SOURCE_DIR}/new/hello.h
  ${CMAKE_CURRENT_SOURCE_DIR}/new/hello.c
)
endif()

#---------------------------------
# 新版本的hello库，源码放在new目录
#---------------------------------
add_executable(test_rule17
  ${CMAKE_CURRENT_SOURCE_DIR}/main.cpp
)
# 以为hello库的头文件没有换过，一直用old目录里的hello.h
target_include_directories(test_rule17 PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/old)
target_link_libraries(test_rule17 hello)