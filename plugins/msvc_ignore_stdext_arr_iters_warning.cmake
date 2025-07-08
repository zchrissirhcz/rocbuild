cmake_minimum_required(VERSION 3.15)
include_guard()

# https://github.com/fmtlib/fmt/issues/3540
# This solves warning in VS2022: warning C4996: 'stdext::checked_array_iterator<T *>': warning STL4043
add_compile_definitions(
  "$<$<COMPILE_LANG_AND_ID:CXX,MSVC>:_SILENCE_STDEXT_ARR_ITERS_DEPRECATION_WARNING>"
)
