cmake_minimum_required(VERSION 3.20)
project(test)

set(CMAKE_INSTALL_PREFIX ${CMAKE_BINARY_DIR}/install)

if(1)
  add_library(foo SHARED IMPORTED)
  # https://cmake.org/cmake/help/latest/prop_tgt/IMPORTED_NO_SONAME.html
  set_target_properties(foo PROPERTIES
    INTERFACE_INCLUDE_DIRECTORIES "${CMAKE_SOURCE_DIR}/foo"
    IMPORTED_LOCATION "${CMAKE_SOURCE_DIR}/foo/libfoo.so"
    IMPORTED_NO_SONAME TRUE # use this when `readelf -d libfoo.so | grep 'SONAME'` got no result
  )
else()
  add_library(foo SHARED
    ${CMAKE_SOURCE_DIR}/foo/foo.c
  )
  target_include_directories(foo PUBLIC
    ${CMAKE_SOURCE_DIR}/foo
  )
endif()

add_executable(test test.c)
target_link_libraries(test PRIVATE foo)

set_target_properties(test PROPERTIES
  INSTALL_RPATH "$ORIGIN/../lib"
)

install(FILES
  ${CMAKE_SOURCE_DIR}/foo/libfoo.so
  DESTINATION lib
)

install(TARGETS test
  RUNTIME DESTINATION bin
)
