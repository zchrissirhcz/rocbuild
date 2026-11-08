# Author: Zhuo Zhang <imzhuo@foxmail.com>
# Homepage: https://github.com/zchrissirhcz/rocbuild
# Last update: 2026-11-07 21:43:00
cmake_minimum_required(VERSION 3.15)
include_guard()

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  add_compile_options("$<$<COMPILE_LANGUAGE:CXX>:-fno-exceptions>")
elseif(MSVC)
    # 1. 先从全局标志中移除默认的 /EHsc
    #string(REPLACE "/EHsc" "" CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
    string(REGEX REPLACE "/EH[a-zA-Z-]*" "" CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")
    
    # 2. 再显式添加禁用异常的 /EHs-c-
    add_compile_options("$<$<COMPILE_LANGUAGE:CXX>:/EHs-c->")
    
    # 3. 让 warning C4530 变为 error
    add_compile_options("/we4530")

    # 4. (可选) 设置 _HAS_EXCEPTIONS 宏，更彻底
    add_compile_definitions("$<$<COMPILE_LANGUAGE:CXX>:_HAS_EXCEPTIONS=0>")

    # NOTE: 编译报错提示: "使用了 C++ 异常处理程序，但未启用展开语义。请指定 /EHsc" .
    # 这句话很没营养。 正确做法：修改报错的代码， 例如用宏包裹起来并关闭使用
endif()