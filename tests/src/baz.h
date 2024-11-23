#pragma once

#ifdef BAZ_EXPORTS
#   if defined(_MSC_VER) || defined(__CYGWIN__) || defined(__MINGW32__)
#       define BAZ_API __declspec(dllexport)
#   elif defined(__GNUC__) && __GNUC__ >= 4
#       define BAZ_API __attribute__ ((visibility ("default")))
#   endif
#else
#   if defined(_MSC_VER) || defined(__CYGWIN__) || defined(__MINGW32__)
#       define BAZ_API __declspec(dllimport)
#   else
#       define BAZ_API
#   endif
#endif

#ifdef __cplusplus
extern "C" {
#endif

BAZ_API int baz();

#ifdef __cplusplus
}
#endif