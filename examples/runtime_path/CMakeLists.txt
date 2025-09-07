cmake_minimum_required(VERSION 3.10)
project(demo)

include(../../basic.cmake)

add_library(foo SHARED foo.c foo.h)

add_library(bar SHARED bar.c bar.h)
target_link_libraries(bar foo)

add_executable(test test.c)
target_link_libraries(test bar)

# set_target_properties(bar PROPERTIES
#   INSTALL_RPATH "$ORIGIN"
# )

# set_target_properties(test PROPERTIES
#   INSTALL_RPATH "$ORIGIN/../lib"
# )

rocbuild_set_install_runtime_path(bar)
rocbuild_set_install_runtime_path(test)

install(TARGETS foo
  LIBRARY DESTINATION lib
)
install(TARGETS bar
  LIBRARY DESTINATION lib
)
install(TARGETS test
  RUNTIME DESTINATION bin
)
