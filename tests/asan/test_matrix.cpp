#include "matrix.hpp"
#include <stdio.h>

int main()
{
    Matrix m(2, 2);
    m(0, 0) = 1;

    Matrix m2 = m;

    printf("bye\n");

    return 0;
}