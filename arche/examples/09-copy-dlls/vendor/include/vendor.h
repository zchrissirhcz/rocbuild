#pragma once

#if defined(_WIN32)
#  ifdef VENDOR_BUILD
#    define VENDOR_API __declspec(dllexport)
#  else
#    define VENDOR_API __declspec(dllimport)
#  endif
#else
#  define VENDOR_API
#endif

VENDOR_API int vendor_value();
