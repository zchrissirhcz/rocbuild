#pragma once

#ifdef FOO_MATH_EXPORTS
#   if defined(_MSC_VER) || defined(__CYGWIN__) || defined(__MINGW32__)
#       define FOO_MATH_API __declspec(dllexport)
#   elif defined(__GNUC__) && __GNUC__ >= 4
#       define FOO_MATH_API __attribute__ ((visibility ("default")))
#   endif
#else
#   if defined(_MSC_VER) || defined(__CYGWIN__) || defined(__MINGW32__)
#       define FOO_MATH_API __declspec(dllimport)
#   else
#       define FOO_MATH_API
#   endif
#endif

#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

FOO_MATH_API
void abs_sort(int n, int* data);

#ifdef __cplusplus
}
#endif

