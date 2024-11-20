add_library(subfoo_static STATIC ../../src/foo.c)
add_library(subfoo_shared SHARED ../../src/foo.c)
add_executable(subhello ../../src/hello.c)