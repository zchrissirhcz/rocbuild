cmake_minimum_required(VERSION 3.15)
include_guard()

# This solves warning when using fopen
# warning C4996: 'fopen': This function or variable may be unsafe. Consider using fopen_s instead
add_compile_definitions(
  "$<$<COMPILE_LANG_AND_ID:C,MSVC>:_CRT_SECURE_NO_WARNINGS>"
  "$<$<COMPILE_LANG_AND_ID:CXX,MSVC>:_CRT_SECURE_NO_WARNINGS>"
)
