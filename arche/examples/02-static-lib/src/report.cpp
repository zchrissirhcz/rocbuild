#include <cstdio>

#include "report.h"

void print_result(const char* label, int value)
{
    std::printf("%-8s = %d\n", label, value);
}
