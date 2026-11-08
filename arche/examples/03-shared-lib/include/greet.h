#pragma once

#if defined(_WIN32)
#  ifdef GREET_BUILD
#    define GREET_API __declspec(dllexport)
#  else
#    define GREET_API __declspec(dllimport)
#  endif
#else
#  define GREET_API
#endif

#include <string>

GREET_API std::string greet(const std::string& name);
