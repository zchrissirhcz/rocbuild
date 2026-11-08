#include <cstdio>

#if defined(USE_NPU_A)
#include "npu_a.h"
#elif defined(USE_NPU_B)
#include "npu_b.h"
#else
#error no NPU selected
#endif

int main()
{
    std::printf("npu_value() = %d\n", npu_value());
    return 0;
}
