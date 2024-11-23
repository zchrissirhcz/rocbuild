#pragma once

#ifdef BAR_EXPORTS
#   if defined(_MSC_VER) || defined(__CYGWIN__) || defined(__MINGW32__)
#       define BAR_API __declspec(dllexport)
#   elif defined(__GNUC__) && __GNUC__ >= 4
#       define BAR_API __attribute__ ((visibility ("default")))
#   endif
#else
#   if defined(_MSC_VER) || defined(__CYGWIN__) || defined(__MINGW32__)
#       define BAR_API __declspec(dllimport)
#   else
#       define BAR_API
#   endif
#endif

#ifdef __cplusplus
extern "C" {
#endif

BAR_API int bar();

#ifdef __cplusplus
}
#endif