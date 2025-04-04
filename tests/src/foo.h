#pragma once

#ifdef FOO_EXPORTS
#   if defined(_MSC_VER) || defined(__CYGWIN__) || defined(__MINGW32__)
#       define FOO_API __declspec(dllexport)
#   elif defined(__GNUC__) && __GNUC__ >= 4
#       define FOO_API __attribute__ ((visibility ("default")))
#   endif
#else
#   if defined(_MSC_VER) || defined(__CYGWIN__) || defined(__MINGW32__)
#       define FOO_API __declspec(dllimport)
#   else
#       define FOO_API
#   endif
#endif

#ifdef __cplusplus
extern "C" {
#endif

FOO_API int foo();

#ifdef __cplusplus
}
#endif