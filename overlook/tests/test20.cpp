// C4267.cpp
// compile by using: cl /W4 C4267.cpp

#include <stdio.h>

void Func1(short)
{
}
void Func2(int)
{
}
void Func3(long)
{
}
void Func4(size_t)
{
}

int main()
{
    size_t bufferSize = 10;
    Func1(bufferSize); // C4267 for all platforms
    Func2(bufferSize); // C4267 only for 64-bit platforms
    Func3(bufferSize); // C4267 only for 64-bit platforms
    Func4(bufferSize); // OK for all platforms
}