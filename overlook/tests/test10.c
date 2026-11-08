#include <stdio.h>

int main()
{
    int data = 10;
    int* ptr = &data;

    int addr = ptr;
    printf("add is %d\n", addr);

    return 0;
}
