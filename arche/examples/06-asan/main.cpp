#include <cstdio>

int main()
{
    int* values = new int[2];
    values[2] = 42;   // 故意越界，用来触发 AddressSanitizer
    std::printf("%d\n", values[2]);
    delete[] values;
    return 0;
}
