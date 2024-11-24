#include <cmath>
#include <iostream>

int main()
{
    float a = 0.5f;
    float b = std::abs(a);
    std::cout << b << std::endl;

    float c = ::abs(a);   // note here: it's proto is: `int abs(int num)`
    std::cout << c << std::endl;

    float d = 3.14;	// note here: double to float conversion happens
    std::cout << d << std::endl;

    return 0;
}
