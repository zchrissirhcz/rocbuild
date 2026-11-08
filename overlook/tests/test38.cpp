#include <iostream>

//void recoup(int n) throw()
void recoup(int n) noexcept
{
    if (n == 0)
        throw std::invalid_argument("cannot be 0");
    printf("valid: %d\n", n);
}

int main()
{
    recoup(0);
    return 0;
}
