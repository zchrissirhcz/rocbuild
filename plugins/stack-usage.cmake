# https://www.cnblogs.com/zjutzz/p/18198833
add_compile_options(
  "$<$<COMPILE_LANG_AND_ID:C,GNU,Clang>:-fstack-usage>"
  "$<$<COMPILE_LANG_AND_ID:CXX,GNU,Clang>:-fstack-usage>"
)