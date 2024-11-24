#include <stdio.h>

int main()
{
    int data;

    if (data > 10)
    {
        printf("data > 10\n");
    }
    else
    {
        printf("data <= 10\n");
    }

    int* ptr;
    printf("*ptr = %d\n", *ptr);

    return 0;
}
