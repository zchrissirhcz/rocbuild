#include <cstdio>

#include "config.h"

extern "C" int foo_value();

int main()
{
    std::printf("APP_VALUE + foo_value() = %d\n", APP_VALUE + foo_value());
    return 0;
}
