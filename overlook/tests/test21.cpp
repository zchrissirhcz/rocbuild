#include <stdio.h>

// C4312.cpp
// compile by using: cl /W1 /LD C4312.cpp
void* f(int i)
{
    return (void*)i; // C4312 for 64-bit targets
}

void* f2(long long i)
{
    return (void*)i; // OK
}

int main()
{
    int* data = (int*)f(10);

    return 0;
}
